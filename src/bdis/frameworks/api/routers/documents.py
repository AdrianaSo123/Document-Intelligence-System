import uuid
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from bdis.frameworks.worker.celery_app import process_document_task
from bdis.domain.entities import JobStatus
from bdis.frameworks.api.dependencies import get_fetch_documents_usecase
from bdis.usecases.fetch_documents import FetchDocumentsUseCase

router = APIRouter(tags=["documents"])

@router.get("/documents")
async def get_documents(use_case: FetchDocumentsUseCase = Depends(get_fetch_documents_usecase)):
    """
    Returns all processed documents from the repository.
    """
    return use_case.execute()

@router.get("/insights")
async def get_insights(use_case: FetchDocumentsUseCase = Depends(get_fetch_documents_usecase)):
    """
    Returns aggregated business insights with correct currency normalization.
    """
    docs = use_case.execute()
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
