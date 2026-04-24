import os
import pytest
from datetime import date
from bdis.domain.entities import DocumentExtraction, JobStatus
from bdis.domain.value_objects import Money
from bdis.infrastructure.database import init_database
from bdis.adapters.repositories import SQLDocumentRepository

def test_sql_repository_save_and_retrieve():
    test_db = "sqlite:///:memory:"
    _, session_factory = init_database(test_db)
    repo = SQLDocumentRepository(session_factory)
    
    extraction = DocumentExtraction(
        document_id="test-doc-001",
        status=JobStatus.VALIDATED,
        raw_text="This is a test document.",
        extracted_data={"company_name": "Test Corp", "amount": 100.0},
        money=Money(100.0),
        company_name="Test Corp",
        due_date=date(2026, 4, 15),
        trace_id="test-trace-001",
        confidence=0.95
    )
    
    # 1. Save
    saved_id = repo.save(extraction)
    assert saved_id == "test-doc-001"
    
    # 2. Retrieve All
    all_docs = repo.get_all()
    assert len(all_docs) >= 1
    found = next((d for d in all_docs if d.document_id == "test-doc-001"), None)
    assert found is not None
    assert found.company_name == "Test Corp"
    assert found.amount_usd == 100.0
    assert found.status == JobStatus.VALIDATED
    
    # 3. Verify types
    assert isinstance(found.due_date, date)
    assert isinstance(found.extracted_data, dict)

    # Cleanup
    if os.path.exists("test_bdis_sql.db"):
        os.remove("test_bdis_sql.db")
