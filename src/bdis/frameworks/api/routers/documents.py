import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from bdis.frameworks.worker.celery_app import process_document_task
from bdis.domain.entities import JobStatus
from bdis.frameworks.api.dependencies import get_fetch_documents_usecase
from bdis.usecases.fetch_documents import FetchDocumentsUseCase

router = APIRouter(tags=["documents"])

@router.post("/documents/upload", status_code=202)
@router.post("/jobs/create", include_in_schema=False)
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

@router.get("/documents")
async def get_documents(use_case: FetchDocumentsUseCase = Depends(get_fetch_documents_usecase)):
    """
    Returns all processed documents from the repository.
    """
    return use_case.execute()

@router.get("/insights")
async def get_insights(use_case: FetchDocumentsUseCase = Depends(get_fetch_documents_usecase)):
    """
    Returns aggregated business insights.
    """
    docs = use_case.execute()
    
    total_revenue = sum(d.amount_usd for d in docs if d.status == JobStatus.VALIDATED)
    overdue_count = len([d for d in docs if d.status == JobStatus.REVIEW_REQUIRED]) # Simple heuristic
    
    return {
        "total_revenue": total_revenue,
        "overdue_count": overdue_count,
        "document_count": len(docs)
    }
