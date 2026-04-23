from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

@dataclass
class DocumentInsight:
    amount_usd: float
    status: str
    due_date: date
    company_name: Optional[str]

    def calculate_risk_flag(self) -> bool:
        """Determines if a document requires manual human review based on business rules."""
        if self.amount_usd > 10000:
            return True
        
        # Determine if invoice is unpaid and older than 30 days past due
        if self.status.lower() == "unpaid":
            thirty_days_ago = date.today() - timedelta(days=30)
            if self.due_date < thirty_days_ago:
                return True
                
        if not self.company_name or not self.company_name.strip():
            return True
            
        return False
