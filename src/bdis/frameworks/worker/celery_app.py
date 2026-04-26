import os
import uuid
from celery import Celery
from bdis.frameworks.pdf_parser import parse_pdf
from bdis.frameworks.api.dependencies import get_processing_pipeline

redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery_app = Celery("bdis_worker", broker=redis_url, backend=redis_url)

# Support for local testing without Redis
celery_app.conf.update(
    task_always_eager=os.getenv("CELERY_TASK_ALWAYS_EAGER", "False").lower() == "true",
    task_eager_propagates=True,
    broker_url=os.getenv("CELERY_BROKER_URL", redis_url),
    result_backend=os.getenv("CELERY_RESULT_BACKEND", redis_url)
)

@celery_app.task(name="process_document_task")
def process_document_task(file_bytes: bytes, raw_text: str = None, expected_data: dict = None, document_id: str = None, trace_id: str = None, filename: str = "document.pdf"):
    # 1. Parse PDF if raw_text not provided
    if not raw_text:
        raw_text = parse_pdf(file_bytes)
    
    # 2. Identity & Traceability
    document_id = document_id or str(uuid.uuid4())
    trace_id = trace_id or str(uuid.uuid4())
    
    # 3. Clean DI: Get the orchestrator from the factory
    pipeline = get_processing_pipeline()
    
    # 4. Execute Core Business Logic (now with storage support)
    extraction = pipeline.execute(
        raw_text=raw_text, 
        document_id=document_id, 
        trace_id=trace_id, 
        file_bytes=file_bytes,
        filename=filename,
        expected_data=expected_data
    )
    
    # 5. Boundary Protection: Map to DTO for serialization
    from bdis.adapters.dtos import ExtractionResultDTO
    dto = ExtractionResultDTO(
        document_id=extraction.document_id,
        status=extraction.status,
        amount_usd=extraction.amount_usd,
        company_name=extraction.company_name,
        confidence=extraction.confidence,
        trace_id=extraction.trace_id,
        created_at=extraction.created_at.isoformat()
    )
    
    return dto.model_dump()
