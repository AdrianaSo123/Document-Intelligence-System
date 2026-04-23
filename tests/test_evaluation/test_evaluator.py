from bdis.adapters.evaluator_adapter import ExactMatchEvaluator

def test_evaluator_perfect_match():
    evaluator = ExactMatchEvaluator()
    extracted = {
        "company_name": "Acme Corp",
        "invoice_id": "INV-123",
        "amount": 1200.50,
        "due_date": "2024-01-01",
        "status": "unpaid"
    }
    expected = {
        "company_name": "Acme Corp",
        "invoice_id": "INV-123",
        "amount": 1200.50,
        "due_date": "2024-01-01",
        "status": "unpaid"
    }
    
    result = evaluator.evaluate("doc_1", extracted, expected)
    assert result.accuracy == 1.0
    assert result.is_perfect_match is True
    assert len(result.missing_fields) == 0
    assert result.confidence_score == 1.0

def test_evaluator_missing_field():
    evaluator = ExactMatchEvaluator()
    extracted = {
        "company_name": "Acme Corp",
        "invoice_id": "INV-123",
        # amount is missing
        "due_date": "2024-01-01",
        "status": "unpaid"
    }
    expected = {
        "company_name": "Acme Corp",
        "invoice_id": "INV-123",
        "amount": 1200.50,
        "due_date": "2024-01-01",
        "status": "unpaid"
    }
    
    result = evaluator.evaluate("doc_2", extracted, expected)
    assert result.accuracy == 0.8  # 4/5 correct
    assert "amount" in result.missing_fields
    assert result.field_scores["amount"] is False
    assert result.field_scores["company_name"] is True
    # Confidence should be lower than accuracy because of the missing field penalty
    assert result.confidence_score == 0.8 * (1.0 - (1/5)) # 0.8 * 0.8 = 0.64

def test_evaluator_incorrect_field():
    evaluator = ExactMatchEvaluator()
    extracted = {
        "company_name": "Acme Corp",
        "invoice_id": "INV-999", # Incorrect
        "amount": 1200.50,
        "due_date": "2024-01-01",
        "status": "unpaid"
    }
    expected = {
        "company_name": "Acme Corp",
        "invoice_id": "INV-123",
        "amount": 1200.50,
        "due_date": "2024-01-01",
        "status": "unpaid"
    }
    
    result = evaluator.evaluate("doc_3", extracted, expected)
    assert result.accuracy == 0.8 # 4/5 correct
    assert len(result.missing_fields) == 0
    assert result.field_scores["invoice_id"] is False
    assert result.confidence_score == 0.8 # 0.8 * 1.0

def test_evaluator_empty_expected():
    evaluator = ExactMatchEvaluator()
    result = evaluator.evaluate("doc_4", {}, {})
    assert result.accuracy == 1.0
    
    result2 = evaluator.evaluate("doc_5", {"extra": "data"}, {})
    assert result2.accuracy == 0.0
