import os
from celery import Celery
from bdis.frameworks.pdf_parser import parse_pdf
from bdis.frameworks.api.dependencies import get_process_document_usecase

redis_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery_app = Celery("bdis_worker", broker=redis_url, backend=redis_url)

@celery_app.task(name="process_document_task")
def process_document_task(file_bytes: bytes):
    # 1. Parse PDF
    raw_text = parse_pdf(file_bytes)
    
    # 2. Get Use Case
    usecase = get_process_document_usecase()
    
    # 3. Execute Core Business Logic
    doc_id = usecase.execute(raw_text, file_bytes)
    return doc_id
