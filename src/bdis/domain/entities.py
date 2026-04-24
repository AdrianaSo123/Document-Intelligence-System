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

@dataclass(frozen=True)
class RawExtraction:
    """
    Typed wrapper for raw AI extraction results.
    Prevents Primitive Obsession at the boundary.
    """
    company_name: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = "USD"
    due_date: Optional[str] = None
    status: Optional[str] = None
    invoice_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.__dict__.items()}

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
            error_message=error_message
        )

    def calculate_risk_flag(self) -> bool:
        """Business logic for identifying high-risk documents."""
        if self.amount_usd > 10000:
            return True
        
        if self.status == JobStatus.REVIEW_REQUIRED:
            return True

        if not self.company_name or not self.company_name.strip():
            return True
            
        return False
