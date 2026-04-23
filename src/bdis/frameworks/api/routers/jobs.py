import uuid
from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException
from bdis.frameworks.worker.celery_app import process_document_task
from bdis.domain.entities import JobStatus

router = APIRouter(prefix="/jobs", tags=["jobs"])

@router.post("/create")
async def create_job(file: UploadFile = File(...)):
    """
    Asynchronously triggers a document processing job.
    Returns a job_id for polling.
    """
    file_bytes = await file.read()
    
    # Generate IDs at the entry point
    document_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())
    
    # Enqueue the task with the IDs
    task = process_document_task.delay(
        file_bytes=file_bytes, 
        document_id=document_id, 
        trace_id=trace_id
    )
    
    return {
        "job_id": task.id,
        "status": JobStatus.PENDING,
        "message": "Job enqueued successfully"
    }

@router.get("/{job_id}")
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
