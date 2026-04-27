import os
import uuid
import logging
from celery import Celery
from bdis.core.config import settings
from bdis.frameworks.pdf_parser import parse_pdf
from bdis.frameworks.api.dependencies import get_processing_pipeline

logger = logging.getLogger(__name__)

celery_app = Celery("bdis_worker", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)

# Support for local testing without Redis
celery_app.conf.update(
    task_always_eager=os.getenv("CELERY_TASK_ALWAYS_EAGER", "False").lower() == "true",
    task_eager_propagates=True
)

@celery_app.task(name="process_document_task")
def process_document_task(s3_uri: str = None, file_bytes: bytes = None, raw_text: str = None, expected_data: dict = None, document_id: str = None, trace_id: str = None, filename: str = "document.pdf"):
    # 1. Clean DI: Get the orchestrator and storage from the factory
    pipeline = get_processing_pipeline()
    from bdis.frameworks.api.dependencies import get_storage
    storage = get_storage()

    # 2. Retrieval Logic (Scalability Fix)
    if s3_uri and not file_bytes:
        logger.info(f"[WORKER] Downloading file from {s3_uri}...")
        file_bytes = storage.download_file(s3_uri)

    # 3. Parse PDF if raw_text not provided
    if not raw_text and file_bytes:
        raw_text = parse_pdf(file_bytes)
    
    if not raw_text:
        logger.error(f"[WORKER] CRITICAL: No text could be extracted for doc_id: {document_id}")
        raw_text = "[ERROR: NO TEXT EXTRACTED]"

    # 4. Identity & Traceability
    document_id = document_id or str(uuid.uuid4())
    trace_id = trace_id or str(uuid.uuid4())
    
    # 5. Execute Core Business Logic
    extraction = pipeline.execute(
        raw_text=raw_text, 
        document_id=document_id, 
        trace_id=trace_id, 
        file_bytes=file_bytes,
        filename=filename,
        expected_data=expected_data
    )
    
    # 6. Return serializable DTO (using domain logic)
    return extraction.to_dto().dict()
