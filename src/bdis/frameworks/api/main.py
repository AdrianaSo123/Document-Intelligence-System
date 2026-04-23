import logging
from fastapi import FastAPI, UploadFile, File, Depends
from bdis.frameworks.worker.celery_app import process_document_task
from bdis.frameworks.api.dependencies import get_repository, get_fetch_documents_usecase
from bdis.usecases.fetch_documents import FetchDocumentsUseCase
from celery.result import AsyncResult

from bdis.frameworks.api.routers import jobs

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="Business Document Intelligence System")

app.include_router(jobs.router)

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    # Read bytes immediately
    file_bytes = await file.read()
    
    # Send to Message Queue instead of blocking
    task = process_document_task.delay(file_bytes)
    
    return {"job_id": task.id, "status": "processing"}

@app.get("/status/{job_id}")
async def get_status(job_id: str):
    task_result = AsyncResult(job_id)
    if task_result.ready():
        return {"job_id": job_id, "status": "completed", "document_id": task_result.result}
    return {"job_id": job_id, "status": "processing"}

@app.get("/documents")
async def get_documents(use_case: FetchDocumentsUseCase = Depends(get_fetch_documents_usecase)):
    # Clean Architecture Enforced: No direct ORM touching
    return use_case.execute()
