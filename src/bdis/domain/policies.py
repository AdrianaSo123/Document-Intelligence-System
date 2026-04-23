from typing import Optional
from bdis.domain.entities import JobStatus
from bdis.domain.evaluation import EvaluationResult

class ProcessingPolicy:
    """
    Encapsulates high-level business rules for document state transitions.
    """
    @staticmethod
    def determine_status(confidence: float, evaluation: Optional[EvaluationResult] = None) -> JobStatus:
        # Business Rule: If evaluation exists and accuracy is low, require review
        if evaluation and evaluation.accuracy < 0.6:
            return JobStatus.REVIEW_REQUIRED
            
        # Business Rule: If confidence is high (>0.85), mark as validated
        if confidence >= 0.85:
            return JobStatus.VALIDATED
            
        # Default: questionable confidence requires review
        if confidence > 0.5:
            return JobStatus.REVIEW_REQUIRED
            
        return JobStatus.FAILED
