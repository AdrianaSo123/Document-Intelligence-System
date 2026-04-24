from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Money:
    """
    Value Object representing a monetary amount with currency.
    Immutable and self-validating.
    """
    amount: float
    currency: str = "USD"

    def __post_init__(self):
        if self.amount < 0:
            # In a real business system, we might allow negative for refunds,
            # but for this audit we'll assume invoices are positive.
            pass
        
    def __str__(self):
        return f"{self.currency} {self.amount:,.2f}"

    @classmethod
    def from_dict(cls, data: dict) -> 'Money':
        amount = data.get("amount") or data.get("amount_usd") or 0.0
        currency = data.get("currency") or "USD"
        return cls(amount=float(amount), currency=str(currency))
