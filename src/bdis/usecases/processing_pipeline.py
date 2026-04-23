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
        sanitizer: ISanitizer
    ):
        self.extractor = extractor
        self.normalizer = normalizer
        self.repository = repository
        self.evaluator = evaluator
        self.sanitizer = sanitizer

    def execute(self, raw_text: str, document_id: str, trace_id: str, expected_data: Dict[str, Any] = None) -> DocumentExtraction:
        logger.info(f"[PIPELINE] [START] trace_id: {trace_id} doc_id: {document_id}")
        
        try:
            # 1. Sanitization (Policy: Never send PII to AI)
            safe_text = self.sanitizer.sanitize(raw_text)
            
            # 2. Extraction
            # Note: Resilience is now handled at the adapter level (Transparent to Use Case)
            extracted_data = self.extractor.extract_schema(safe_text)
            
            # 3. Normalization
            normalized_data = self.normalizer.normalize(extracted_data)
            
            # 4. Evaluation (vs Ground Truth)
            evaluation_result = None
            if expected_data:
                evaluation_result = self.evaluator.evaluate(document_id, normalized_data, expected_data)
            
            # 5. Determine Final Status (Policy Encapsulated)
            confidence = evaluation_result.confidence_score if evaluation_result else 0.8
            status = ProcessingPolicy.determine_status(confidence, evaluation_result)
            
            result = DocumentExtraction.from_normalized_data(
                document_id=document_id,
                trace_id=trace_id,
                status=status,
                raw_text=safe_text,
                normalized_data=normalized_data,
                evaluation=evaluation_result,
                confidence=confidence
            )
            
            # 6. Persistence
            logger.info(f"[PIPELINE] [PERSISTENCE] START doc_id: {document_id}")
            self.repository.save(result) 
            
            logger.info(f"[PIPELINE] [COMPLETE] doc_id: {document_id} status: {status}")
            return result

        except Exception as e:
            logger.error(f"[PIPELINE] [FAILED] doc_id: {document_id} error: {e}")
            result = DocumentExtraction(
                document_id=document_id,
                status=JobStatus.FAILED,
                raw_text=raw_text,
                extracted_data={},
                trace_id=trace_id,
                error_message=str(e)
            )
            # Persist the failure
            self.repository.save(result)
            return result
