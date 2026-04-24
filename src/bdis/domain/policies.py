from typing import Optional
from bdis.domain.entities import JobStatus
from bdis.domain.evaluation import EvaluationResult

class ProcessingPolicy:
    """
    Encapsulates high-level business rules for document state transitions.
    """
    VALIDATION_THRESHOLD = 0.85
    MIN_CONFIDENCE_THRESHOLD = 0.5
    DEFAULT_CONFIDENCE = 0.8
    MIN_ACCURACY_THRESHOLD = 0.6

    @staticmethod
    def determine_status(confidence: float, evaluation: Optional[EvaluationResult] = None) -> JobStatus:
        # Business Rule: If evaluation exists and accuracy is low, require review
        if evaluation and evaluation.accuracy < ProcessingPolicy.MIN_ACCURACY_THRESHOLD:
            return JobStatus.REVIEW_REQUIRED
            
        # Business Rule: If confidence is high, mark as validated
        if confidence >= ProcessingPolicy.VALIDATION_THRESHOLD:
            return JobStatus.VALIDATED
            
        # Default: questionable confidence requires review
        if confidence > ProcessingPolicy.MIN_CONFIDENCE_THRESHOLD:
            return JobStatus.REVIEW_REQUIRED
            
        return JobStatus.FAILED
