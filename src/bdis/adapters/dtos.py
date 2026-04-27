from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class LLMResponseBoundaryDTO(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    company_name: Optional[str] = None
    invoice_id: Optional[str] = None
    amount_usd: Optional[float] = None
    # Add regex to enforce ISO format strings if desired, or validate later
    currency: Optional[str] = Field(None, max_length=3) 
    due_date: Optional[str] = None # Expecting YYYY-MM-DD
    status: Optional[str] = None

class ExtractionResultDTO(BaseModel):
    document_id: str
    status: str
    amount_usd: float
    currency: str = "USD"
    company_name: Optional[str]
    confidence: float
    is_high_risk: bool = False
    trace_id: str
    created_at: str
    s3_uri: Optional[str] = None
    raw_text: Optional[str] = None
