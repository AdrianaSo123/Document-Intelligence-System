from dataclasses import dataclass, field
from typing import Dict

@dataclass
class EvaluationResult:
    document_id: str
    accuracy: float
    field_scores: Dict[str, bool]
    missing_fields: list[str] = field(default_factory=list)
    confidence_score: float = 0.0

    @property
    def is_perfect_match(self) -> bool:
        """Returns True if accuracy is 1.0."""
        return self.accuracy == 1.0
