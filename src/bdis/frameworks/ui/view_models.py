from pydantic import BaseModel, Field
from typing import Optional

class DashboardViewModel(BaseModel):
    document_id: str
    company_name: str = Field(default="Unknown Entity")
    amount_usd: float = Field(default=0.0)
    status: str = Field(default="unknown")
    due_date: Optional[str] = None
    
    @property
    def is_high_risk(self) -> bool:
        """UI-Specific Business Logic (Derived State)"""
        return self.status.lower() == "unpaid" and self.amount_usd > 10000.0

class ErrorViewModel(BaseModel):
    is_error: bool = True
    error_message: str
