from typing import Optional
from bdis.domain.entities import JobStatus
from bdis.domain.evaluation import EvaluationResult

class ProcessingPolicy:
    """
    Encapsulates high-level business rules for document state transitions.
    Thresholds are defined as class attributes to allow for easier configuration.
    """
    VALIDATION_THRESHOLD = 0.85
    MIN_CONFIDENCE_THRESHOLD = 0.5
    DEFAULT_CONFIDENCE = 0.8
    MIN_ACCURACY_THRESHOLD = 0.6

    @classmethod
    def determine_status(cls, confidence: float, evaluation: Optional[EvaluationResult] = None) -> JobStatus:
        # Business Rule: If evaluation exists and accuracy is low, require review
        if evaluation and evaluation.accuracy < cls.MIN_ACCURACY_THRESHOLD:
            return JobStatus.REVIEW_REQUIRED
            
        # Business Rule: If confidence is high, mark as validated
        if confidence >= cls.VALIDATION_THRESHOLD:
            return JobStatus.VALIDATED
            
        # Default: questionable confidence requires review
        if confidence > cls.MIN_CONFIDENCE_THRESHOLD:
            return JobStatus.REVIEW_REQUIRED
            
        return JobStatus.FAILED
