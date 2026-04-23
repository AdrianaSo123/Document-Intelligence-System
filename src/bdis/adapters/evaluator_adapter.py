from typing import Dict, Any
from bdis.ports.evaluator import IEvaluator
from bdis.domain.evaluation import EvaluationResult

class ExactMatchEvaluator(IEvaluator):
    """
    Evaluator that calculates accuracy based on strict exact matches.
    """
    def evaluate(self, document_id: str, extracted_data: Dict[str, Any], expected_data: Dict[str, Any]) -> EvaluationResult:
        field_scores = {}
        missing_fields = []
        total_expected_fields = len(expected_data)
        correct_fields = 0
        
        if total_expected_fields == 0:
            return EvaluationResult(
                document_id=document_id,
                accuracy=1.0 if not extracted_data else 0.0,
                field_scores={},
                missing_fields=[],
                confidence_score=1.0 if not extracted_data else 0.0
            )

        for key, expected_val in expected_data.items():
            if key not in extracted_data or extracted_data[key] is None:
                field_scores[key] = False
                missing_fields.append(key)
            else:
                extracted_val = extracted_data[key]
                # Coerce types for fair comparison where reasonable, or expect strict match?
                # For a baseline evaluator, we use strict equality, but handle float vs int.
                if isinstance(expected_val, (int, float)) and isinstance(extracted_val, (int, float)):
                    match = float(expected_val) == float(extracted_val)
                else:
                    match = expected_val == extracted_val
                
                field_scores[key] = match
                if match:
                    correct_fields += 1

        accuracy = correct_fields / total_expected_fields

        # Confidence heuristic: penalize missing fields heavily, scale with correct fields
        confidence = accuracy * (1.0 - (len(missing_fields) / total_expected_fields))

        return EvaluationResult(
            document_id=document_id,
            accuracy=accuracy,
            field_scores=field_scores,
            missing_fields=missing_fields,
            confidence_score=confidence
        )
