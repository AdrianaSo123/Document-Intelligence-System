from fastapi import FastAPI, UploadFile, File
from bdis.frameworks.worker.celery_app import process_document_task
from celery.result import AsyncResult

app = FastAPI(title="Business Document Intelligence System")

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
