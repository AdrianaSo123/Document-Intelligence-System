import os
import uuid
from celery import Celery
from bdis.frameworks.pdf_parser import parse_pdf
from bdis.frameworks.api.dependencies import get_process_document_usecase

redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery_app = Celery("bdis_worker", broker=redis_url, backend=redis_url)

@celery_app.task(name="process_document_task")
def process_document_task(file_bytes: bytes, raw_text: str = None, expected_data: dict = None, document_id: str = None, trace_id: str = None):
    # 1. Parse PDF if raw_text not provided
    if not raw_text:
        raw_text = parse_pdf(file_bytes)
    
    # 2. Identity & Traceability
    document_id = document_id or str(uuid.uuid4())
    trace_id = trace_id or str(uuid.uuid4())
    
    # 3. Clean DI: Get the orchestrator from the factory
    pipeline = get_process_document_usecase()
    
    # 4. Execute Core Business Logic
    extraction = pipeline.execute(raw_text, document_id, trace_id, expected_data=expected_data)
    
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
