import pytest
from unittest.mock import Mock, MagicMock
from bdis.usecases.processing_pipeline import ProcessingPipeline
from bdis.domain.entities import DocumentExtraction, JobStatus
from bdis.domain.evaluation import EvaluationResult

@pytest.fixture
def mock_dependencies():
    return {
        "extractor": Mock(),
        "normalizer": Mock(),
        "repository": Mock(),
        "evaluator": Mock(),
        "sanitizer": Mock(),
        "storage": Mock()
    }

def test_pipeline_execution_success(mock_dependencies):
    # Setup
    pipeline = ProcessingPipeline(**mock_dependencies)
    
    mock_dependencies["sanitizer"].sanitize.return_value = "safe text"
    from bdis.domain.entities import RawExtraction
    mock_dependencies["extractor"].extract_schema.return_value = RawExtraction(company_name="Test", amount=100.0)
    mock_dependencies["normalizer"].normalize.return_value = {"amount": 100.0, "company_name": "Test"}
    mock_dependencies["evaluator"].evaluate.return_value = EvaluationResult(
        document_id="doc1", accuracy=1.0, field_scores={}, confidence_score=0.9
    )
    
    # Execute
    result = pipeline.execute(
        raw_text="dirty text",
        document_id="doc1",
        trace_id="trace1",
        expected_data={"company_name": "Test", "amount": 100.0}
    )
    
    # Assertions
    assert result.status == JobStatus.VALIDATED
    assert result.raw_text == "safe text"
    assert result.confidence == 0.9
    
    mock_dependencies["sanitizer"].sanitize.assert_called_once_with("dirty text")
    mock_dependencies["repository"].save.assert_called_once()

def test_pipeline_execution_failure(mock_dependencies):
    # Setup
    pipeline = ProcessingPipeline(**mock_dependencies)
    mock_dependencies["sanitizer"].sanitize.side_effect = Exception("Sanitization failed")
    
    # Execute
    result = pipeline.execute(
        raw_text="dirty text",
        document_id="doc1",
        trace_id="trace1"
    )
    
    # Assertions
    assert result.status == JobStatus.FAILED
    assert "Sanitization failed" in result.error_message
    mock_dependencies["repository"].save.assert_called_once()
