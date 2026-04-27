import re
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime
from bdis.ports.normalizer import INormalizer

class NormalizationStrategy(ABC):
    @abstractmethod
    def apply(self, data: Dict[str, Any]) -> Dict[str, Any]:
        pass

class AmountNormalizer(NormalizationStrategy):
    def apply(self, data: Dict[str, Any]) -> Dict[str, Any]:
        val = data.get("amount") or data.get("amount_usd")
        if val is not None:
            data["amount"] = self._to_float(val)
        return data

    def _to_float(self, val: Any) -> float:
        if isinstance(val, (int, float)): return float(val)
        clean = re.sub(r'[^\d.]', '', str(val))
        try: return float(clean)
        except: return 0.0

class DateNormalizer(NormalizationStrategy):
    def apply(self, data: Dict[str, Any]) -> Dict[str, Any]:
        val = data.get("due_date")
        if not val:
            return data
            
        try:
            s_val = str(val).strip()
            # 1. Standard ISO Format (YYYY-MM-DD)
            if re.match(r'^\d{4}-\d{2}-\d{2}$', s_val):
                data["due_date"] = datetime.strptime(s_val, "%Y-%m-%d").date()
                return data

            # 2. US Format (MM/DD/YYYY)
            m_us = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})$', s_val)
            if m_us:
                s_val = f"{m_us.group(3)}-{m_us.group(1).zfill(2)}-{m_us.group(2).zfill(2)}"
                data["due_date"] = datetime.strptime(s_val, "%Y-%m-%d").date()
                return data

            # 3. Descriptive Month Format (e.g., October 23, 2026)
            for fmt in ["%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d %b %Y"]:
                try:
                    data["due_date"] = datetime.strptime(s_val, fmt).date()
                    return data
                except ValueError:
                    continue

        except Exception:
            pass
        return data

class StatusNormalizer(NormalizationStrategy):
    def apply(self, data: Dict[str, Any]) -> Dict[str, Any]:
        val = data.get("status")
        if val:
            s = str(val).lower().strip()
            if s in ["paid", "settled"]: data["status"] = "paid"
            elif s in ["unpaid", "pending", "due", "overdue"]: data["status"] = "unpaid"
            else: data["status"] = "unknown"
        return data

class DocumentNormalizer(INormalizer):
    """
    Plugin-based normalizer following the Open-Closed Principle.
    """
    def __init__(self, strategies: List[NormalizationStrategy] = None):
        self.strategies = strategies or [
            AmountNormalizer(),
            DateNormalizer(),
            StatusNormalizer()
        ]

    def normalize(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        normalized = raw_data.copy()
        for strategy in self.strategies:
            normalized = strategy.apply(normalized)
        return normalized
