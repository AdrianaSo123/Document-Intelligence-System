import uuid
import logging
from typing import Dict, Any, Optional
from bdis.domain.entities import DocumentExtraction, JobStatus
from bdis.ports.extraction_service import IExtractionService
from bdis.ports.normalizer import INormalizer
from bdis.ports.document_repository import IDocumentRepository
from bdis.ports.evaluator import IEvaluator
from bdis.domain.policies import ProcessingPolicy
from bdis.ports.sanitizer import ISanitizer
from bdis.ports.file_storage import IFileStorage

logger = logging.getLogger(__name__)

class ProcessingPipeline:
    """
    Clean Orchestrator: Coordinates the flow of data through abstracted Ports.
    """
    def __init__(
        self,
        extractor: IExtractionService,
        normalizer: INormalizer,
        repository: IDocumentRepository,
        evaluator: IEvaluator,
        sanitizer: ISanitizer,
        storage: IFileStorage
    ):
        self.extractor = extractor
        self.normalizer = normalizer
        self.repository = repository
        self.evaluator = evaluator
        self.sanitizer = sanitizer
        self.storage = storage

    def execute(self, raw_text: str, document_id: str, trace_id: str, workspace_id: str, file_bytes: bytes = None, filename: str = "document.pdf", expected_data: Dict[str, Any] = None) -> DocumentExtraction:
        logger.info(f"[PIPELINE] [START] trace_id: {trace_id} doc_id: {document_id}")
        
        s3_uri = None
        if file_bytes:
            logger.info(f"[PIPELINE] [STORAGE] Archiving original file...")
            s3_uri = self.storage.upload_file(workspace_id, document_id, file_bytes, filename)
            
        try:
            # 1. Sanitization (Policy: Never send PII to AI)
            safe_text = self.sanitizer.sanitize(raw_text)
            
            # 2. Extraction (Spec Compliance: Retry once on failure)
            extraction_result = None
            last_error = None
            for attempt in range(2):
                try:
                    extraction_result = self.extractor.extract_schema(safe_text)
                    break # Success!
                except Exception as e:
                    logger.warning(f"[PIPELINE] Extraction attempt {attempt+1} failed: {e}")
                    last_error = e
                    if attempt == 0: continue # Retry
            
            if not extraction_result:
                raise last_error or Exception("Extraction failed after retries")
            
            # 3. Normalization (Expects a dict for strategy pattern)
            normalized_data = self.normalizer.normalize(extraction_result.to_dict())
            
            # 4. Evaluation (vs Ground Truth)
            evaluation_result = None
            if expected_data:
                evaluation_result = self.evaluator.evaluate(document_id, normalized_data, expected_data)
            
            # 5. Determine Final Status (Policy Encapsulated)
            confidence = evaluation_result.confidence_score if evaluation_result else ProcessingPolicy.DEFAULT_CONFIDENCE
            status = ProcessingPolicy.determine_status(confidence, evaluation_result)
            
            result = DocumentExtraction.create(
                document_id=document_id,
                trace_id=trace_id,
                status=status,
                raw_text=safe_text,
                normalized_data=normalized_data,
                due_date=normalized_data.get("due_date"),
                evaluation=evaluation_result,
                confidence=confidence,
                s3_uri=s3_uri
            )
            
            # 6. Persistence
            logger.info(f"[PIPELINE] [PERSISTENCE] START doc_id: {document_id}")
            self.repository.save(workspace_id, result)
            
            logger.info(f"[PIPELINE] [COMPLETE] doc_id: {document_id} status: {status}")
            return result

        except Exception as e:
            logger.error(f"[PIPELINE] [FAILED] doc_id: {document_id} error: {e}")
            result = DocumentExtraction.create(
                document_id=document_id,
                trace_id=trace_id,
                status=JobStatus.FAILED,
                raw_text=raw_text,
                normalized_data={},
                error_message=str(e)
            )
            # Persist the failure
            self.repository.save(workspace_id, result)
            return result
