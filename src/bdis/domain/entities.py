from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional, Dict, Any
from enum import Enum
from bdis.domain.evaluation import EvaluationResult

class JobStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    VALIDATED = "VALIDATED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    FAILED = "FAILED"

from bdis.domain.value_objects import Money

from pydantic import BaseModel, Field

class RawExtraction(BaseModel):
    """
    Typed wrapper for raw AI extraction results.
    Prevents Primitive Obsession at the boundary.
    """
    company_name: Optional[str] = None
    amount: Optional[float] = Field(None, alias="amount_usd")
    currency: Optional[str] = "USD"
    due_date: Optional[str] = None
    status: Optional[str] = None
    invoice_id: Optional[str] = None
    risk_flag: Optional[bool] = None

    class Config:
        populate_by_name = True

    def to_dict(self):
        return self.model_dump()

@dataclass
class DocumentExtraction:
    """
    The central domain entity representing a processed document and its insights.
    """
    document_id: str
    status: JobStatus
    raw_text: str
    extracted_data: Dict[str, Any]
    
    # Insights (Value Objects & Mapped Types)
    money: Money = field(default_factory=lambda: Money(0.0))
    company_name: Optional[str] = None
    due_date: Optional[date] = None
    s3_uri: Optional[str] = None
    
    # Metadata & Evaluation
    evaluation: Optional[EvaluationResult] = None
    trace_id: Optional[str] = None
    confidence: float = 0.0
    error_message: Optional[str] = None
    created_at: date = field(default_factory=date.today)

    @property
    def amount_usd(self) -> float:
        """Legacy helper for backward compatibility with repositories/UI."""
        return self.money.amount

    @classmethod
    def create(
        cls, 
        document_id: str, 
        trace_id: str, 
        status: JobStatus, 
        raw_text: str, 
        normalized_data: Dict[str, Any], 
        due_date: Optional[date] = None,
        evaluation: Optional[EvaluationResult] = None,
        confidence: float = 0.0,
        s3_uri: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> 'DocumentExtraction':
        """
        Pure Domain Factory: Expects valid objects, not raw strings.
        """
        return cls(
            document_id=document_id,
            trace_id=trace_id,
            status=status,
            raw_text=raw_text,
            extracted_data=normalized_data,
            money=Money.from_dict(normalized_data),
            company_name=normalized_data.get("company_name"),
            due_date=due_date,
            confidence=confidence,
            evaluation=evaluation,
            s3_uri=s3_uri,
            error_message=error_message
        )

    @property
    def currency(self) -> str:
        return self.money.currency

    def calculate_risk_flag(self) -> bool:
        """Unified High-Risk Policy (Phase 4 Refactor)"""
        if self.amount_usd >= 10000.0: return True
        if self.amount_usd >= 1000.0 and self.status == JobStatus.REVIEW_REQUIRED: return True
        if not self.company_name: return True
        return False

    def to_dto(self) -> Any:
        """
        Maps the domain entity to the cross-layer ExtractionResultDTO.
        This centralizes the mapping logic to prevent duplication in workers/APIs.
        """
        from bdis.adapters.dtos import ExtractionResultDTO
        return ExtractionResultDTO(
            document_id=self.document_id,
            status=self.status,
            amount_usd=self.amount_usd,
            currency=self.currency,
            company_name=self.company_name,
            confidence=self.confidence,
            is_high_risk=self.calculate_risk_flag(),
            trace_id=self.trace_id,
            created_at=self.created_at.isoformat(),
            s3_uri=self.s3_uri,
            raw_text=self.raw_text
        )
