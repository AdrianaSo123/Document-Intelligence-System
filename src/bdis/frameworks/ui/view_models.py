from pydantic import BaseModel, Field
from typing import Optional

class DashboardViewModel(BaseModel):
    document_id: str
    company_name: str = Field(default="Unknown Entity")
    amount_usd: float = Field(default=0.0)
    currency: str = Field(default="USD")
    status: str = Field(default="unknown")
    due_date: Optional[str] = None
    s3_uri: Optional[str] = None
    is_high_risk: bool = Field(default=False)
    confidence: float = Field(default=0.0)
    created_at: Optional[str] = None
    trace_id: Optional[str] = None
    raw_text: Optional[str] = None

class ErrorViewModel(BaseModel):
    is_error: bool = True
    error_message: str
