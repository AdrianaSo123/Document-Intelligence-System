import uuid
import logging
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from bdis.frameworks.worker.celery_app import process_document_task
from bdis.domain.entities import JobStatus
from bdis.frameworks.api.dependencies import get_storage, get_request_context, audit_event, jobs_create, jobs_get, jobs_list
from bdis.core.auth import RequestContext, role_allows_write

logger = logging.getLogger(__name__)

router = APIRouter(tags=["jobs"])

def _require_workspace_match(route_workspace_id: str, ctx: RequestContext) -> None:
    if route_workspace_id != ctx.workspace_id:
        raise HTTPException(status_code=403, detail="Route workspace_id does not match authenticated workspace.")

@router.post("/jobs/create", status_code=202)
@router.post("/documents/upload", include_in_schema=False)
async def create_job(
    file: UploadFile = File(...),
    storage=Depends(get_storage),
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Asynchronously triggers a document processing job.
    Refactored to upload to S3 BEFORE enqueuing to protect the message broker.
    """
    if not role_allows_write(ctx.role):
        raise HTTPException(status_code=403, detail="Role is not permitted to upload/enqueue jobs.")

    file_bytes = await file.read()
    
    # 1. Generate IDs (used for storage partitioning + job identity)
    document_id = str(uuid.uuid4())
    trace_id = str(uuid.uuid4())

    # 2. Immediate Storage (Scalability fix)
    logger.info(f"[API] Archiving file '{file.filename}' to storage before enqueuing...")
    s3_uri = storage.upload_file(ctx.workspace_id, document_id, file_bytes, file.filename)
    
    if not s3_uri:
        raise HTTPException(status_code=500, detail="Initial file storage failed. Pipeline aborted.")

    # 3. Enqueue the task with the S3 URI instead of raw bytes
    task = process_document_task.delay(
        s3_uri=s3_uri, 
        document_id=document_id, 
        trace_id=trace_id,
        workspace_id=ctx.workspace_id,
        filename=file.filename,
        job_id=None,  # filled below for clarity; celery sets task.id after enqueue
    )

    jobs_create(ctx, job_id=task.id, document_id=document_id, trace_id=trace_id)

    audit_event(
        ctx,
        event_type="job.enqueued",
        resource_type="job",
        resource_id=task.id,
        metadata={"filename": file.filename},
    )

    audit_event(
        ctx,
        event_type="document.uploaded",
        resource_type="document",
        resource_id=document_id,
        metadata={"filename": file.filename},
    )
    
    return {
        "job_id": task.id,
        "status": JobStatus.PENDING,
        "message": "Job enqueued successfully via S3 URI"
    }

@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Returns the current status and result of a job.
    """
    # Phase 6C1: authoritative status is the relational DB, scoped by workspace_id.
    return jobs_get(ctx, job_id)


@router.post("/workspaces/{workspace_id}/jobs", status_code=202)
async def create_workspace_job(
    workspace_id: str,
    file: UploadFile = File(...),
    storage=Depends(get_storage),
    ctx: RequestContext = Depends(get_request_context),
):
    _require_workspace_match(workspace_id, ctx)
    return await create_job(file=file, storage=storage, ctx=ctx)


@router.get("/workspaces/{workspace_id}/jobs/{job_id}")
async def get_workspace_job_status(
    workspace_id: str,
    job_id: str,
    ctx: RequestContext = Depends(get_request_context),
):
    _require_workspace_match(workspace_id, ctx)
    return jobs_get(ctx, job_id)


@router.get("/workspaces/{workspace_id}/jobs")
async def list_workspace_jobs(
    workspace_id: str,
    ctx: RequestContext = Depends(get_request_context),
):
    _require_workspace_match(workspace_id, ctx)
    return jobs_list(ctx)
