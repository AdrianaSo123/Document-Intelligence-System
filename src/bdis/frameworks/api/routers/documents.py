import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from bdis.frameworks.worker.celery_app import process_document_task
from bdis.domain.entities import JobStatus
from bdis.frameworks.api.dependencies import get_fetch_documents_usecase, get_request_context
from bdis.usecases.fetch_documents import FetchDocumentsUseCase
from bdis.core.auth import RequestContext

router = APIRouter(tags=["documents"])

def _require_workspace_match(route_workspace_id: str, ctx: RequestContext) -> None:
    if route_workspace_id != ctx.workspace_id:
        raise HTTPException(status_code=403, detail="Route workspace_id does not match authenticated workspace.")

@router.get("/documents")
async def get_documents(
    use_case: FetchDocumentsUseCase = Depends(get_fetch_documents_usecase),
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Returns all processed documents from the repository.
    """
    return use_case.execute(ctx.workspace_id)


@router.get("/workspaces/{workspace_id}/documents")
async def get_workspace_documents(
    workspace_id: str,
    use_case: FetchDocumentsUseCase = Depends(get_fetch_documents_usecase),
    ctx: RequestContext = Depends(get_request_context),
):
    _require_workspace_match(workspace_id, ctx)
    return use_case.execute(ctx.workspace_id)

@router.get("/insights")
async def get_insights(
    use_case: FetchDocumentsUseCase = Depends(get_fetch_documents_usecase),
    ctx: RequestContext = Depends(get_request_context),
):
    """
    Returns aggregated business insights with correct currency normalization.
    """
    docs = use_case.execute(ctx.workspace_id)
    from bdis.core.financials import convert_to_usd
    
    total_revenue_usd = 0.0
    currency_counts = {}
    
    for d in docs:
        if d.status == JobStatus.VALIDATED:
            total_revenue_usd += convert_to_usd(d.amount_usd, d.currency)
            
        currency_counts[d.currency] = currency_counts.get(d.currency, 0) + 1
    
    overdue_count = len([d for d in docs if d.status == JobStatus.REVIEW_REQUIRED])
    
    return {
        "total_revenue_usd": total_revenue_usd,
        "overdue_count": overdue_count,
        "document_count": len(docs),
        "currency_breakdown": currency_counts
    }


@router.get("/workspaces/{workspace_id}/insights")
async def get_workspace_insights(
    workspace_id: str,
    use_case: FetchDocumentsUseCase = Depends(get_fetch_documents_usecase),
    ctx: RequestContext = Depends(get_request_context),
):
    _require_workspace_match(workspace_id, ctx)
    return await get_insights(use_case=use_case, ctx=ctx)
