import uuid
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from bdis.frameworks.worker.celery_app import process_document_task
from bdis.domain.entities import JobStatus
from bdis.frameworks.api.dependencies import get_storage

logger = logging.getLogger(__name__)

router = APIRouter(tags=["jobs"])

@router.post("/jobs/create", status_code=202)
@router.post("/documents/upload", include_in_schema=False)
async def create_job(file: UploadFile = File(...), storage = Depends(get_storage)):
    """
    Asynchronously triggers a document processing job.
    Refactored to upload to S3 BEFORE enqueuing to protect the message broker.
    """
    file_bytes = await file.read()
    
    # 1. Immediate Storage (Scalability fix)
    logger.info(f"[API] Archiving file '{file.filename}' to S3 before enqueuing...")
    s3_uri = storage.upload_file(file_bytes, file.filename)
    
    if not s3_uri:
        raise HTTPException(status_code=500, detail="Initial file storage failed. Pipeline aborted.")

    # 2. Generate IDs
    document_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    
    # 3. Enqueue the task with the S3 URI instead of raw bytes
    task = process_document_task.delay(
        s3_uri=s3_uri, 
        document_id=document_id, 
        trace_id=trace_id,
        filename=file.filename
    )
    
    return {
        "job_id": task.id,
        "status": JobStatus.PENDING,
        "message": "Job enqueued successfully via S3 URI"
    }

@router.get("/jobs/{job_id}")
async def get_job_status(job_id: str):
    """
    Returns the current status and result of a job.
    """
    from bdis.frameworks.worker.celery_app import celery_app
    res = celery_app.AsyncResult(job_id)
    
    if res.ready():
        if res.failed():
            return {"job_id": job_id, "status": JobStatus.FAILED, "error": str(res.result)}
        return {"job_id": job_id, "status": "COMPLETE", "result": res.result}
    
    return {"job_id": job_id, "status": res.status}
