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

@dataclass
class DocumentExtraction:
    """
    The central domain entity representing a processed document and its insights.
    """
    document_id: str
    status: JobStatus
    raw_text: str
    extracted_data: Dict[str, Any]
    
    # Insights (Calculated or mapped)
    amount_usd: float = 0.0
    company_name: Optional[str] = None
    due_date: Optional[date] = None
    s3_uri: Optional[str] = None
    
    # Metadata & Evaluation
    evaluation: Optional[EvaluationResult] = None
    trace_id: Optional[str] = None
    confidence: float = 0.0
    error_message: Optional[str] = None
    created_at: date = field(default_factory=date.today)

    @classmethod
    def from_normalized_data(
        cls, 
        document_id: str, 
        trace_id: str, 
        status: JobStatus, 
        raw_text: str, 
        normalized_data: Dict[str, Any], 
        evaluation: Optional[EvaluationResult] = None,
        confidence: float = 0.0,
        error_message: Optional[str] = None
    ) -> 'DocumentExtraction':
        due_date = normalized_data.get("due_date")
        if isinstance(due_date, str):
            try:
                due_date = date.fromisoformat(due_date)
            except ValueError:
                due_date = None

        return cls(
            document_id=document_id,
            trace_id=trace_id,
            status=status,
            raw_text=raw_text,
            extracted_data=normalized_data,
            amount_usd=normalized_data.get("amount", 0.0),
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
