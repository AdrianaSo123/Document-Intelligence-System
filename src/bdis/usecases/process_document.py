from datetime import date
from typing import Dict, Any

from bdis.domain.entities import DocumentInsight
from bdis.ports.extraction_service import IExtractionService
from bdis.ports.document_repository import IDocumentRepository
from bdis.adapters.dtos import LLMResponseBoundaryDTO

class ProcessDocumentUseCase:
    """
    Orchestrates the ingestion, extraction, rule calculation, and saving of a document.
    """
    def __init__(self, extractor: IExtractionService, repository: IDocumentRepository):
        self.extractor = extractor
        self.repository = repository

    def execute(self, raw_text: str) -> str:
        """
        Executes the business logic workflow.
        Returns the ID of the saved record.
        """
        # 1. Ask Extractor to get structured data
        raw_dict = self.extractor.extract_schema(raw_text)
        
        # Note: Sprint 2 uses Pydantic DTO
        dto = LLMResponseBoundaryDTO(**raw_dict)
        
        parsed_date = date.today()
        if dto.due_date:
             try:
                 parsed_date = date.fromisoformat(dto.due_date)
             except ValueError:
                 pass
        
        amount = dto.amount_usd if dto.amount_usd is not None else 0.0

        status = dto.status if dto.status is not None else "unknown"
        company_name = dto.company_name if dto.company_name is not None else ""

        # 2. Construct Pure Domain Entity
        insight = DocumentInsight(
            amount_usd=float(amount),
            status=status,
            due_date=parsed_date,
            company_name=company_name
        )
        
        # (Optional Workflow Step) Calculate risk flag -- Though it's self-calculating,
        # we might want to log it or handle it before saving eventually.
        # flag = insight.calculate_risk_flag()
        
        # 3. Save via Repository
        saved_id = self.repository.save(insight)
        
        return saved_id
