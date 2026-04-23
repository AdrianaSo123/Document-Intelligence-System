from abc import ABC, abstractmethod
from typing import Dict, Any
from bdis.domain.evaluation import EvaluationResult

class IEvaluator(ABC):
    """
    Port for evaluating extracted document data against ground truth expectations.
    """
    @abstractmethod
    def evaluate(self, document_id: str, extracted_data: Dict[str, Any], expected_data: Dict[str, Any]) -> EvaluationResult:
        """
        Compares extracted data against expected data and returns a structured EvaluationResult.
        """
        pass
