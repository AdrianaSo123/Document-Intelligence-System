import os
import pytest
from datetime import date
from bdis.domain.entities import DocumentExtraction, JobStatus
from bdis.domain.value_objects import Money
from bdis.infrastructure.database import init_database
from bdis.adapters.repositories import SQLDocumentRepository
from bdis.core.tenancy import DEFAULT_WORKSPACE_ID
from bdis.infrastructure.persistence.models import Base

def test_sql_repository_save_and_retrieve():
    test_db = "sqlite:///:memory:"
    engine, session_factory = init_database(test_db)
    Base.metadata.create_all(engine)
    repo = SQLDocumentRepository(session_factory)
    
    extraction = DocumentExtraction(
        document_id="test-doc-001",
        status=JobStatus.VALIDATED,
        raw_text="This is a test document.",
        extracted_data={"company_name": "Test Corp", "amount": 100.0},
        money=Money(100.0, "EUR"),
        company_name="Test Corp",
        due_date=date(2026, 4, 15),
        trace_id="test-trace-001",
        confidence=0.95
    )
    
    # 1. Save
    saved_id = repo.save(DEFAULT_WORKSPACE_ID, extraction)
    assert saved_id == "test-doc-001"
    
    # 2. Retrieve All
    all_docs = repo.get_all(DEFAULT_WORKSPACE_ID)
    assert len(all_docs) >= 1
    found = next((d for d in all_docs if d.document_id == "test-doc-001"), None)
    assert found is not None
    assert found.company_name == "Test Corp"
    assert found.amount_usd == 100.0
    assert found.currency == "EUR"
    assert found.status == JobStatus.VALIDATED
    
    # 3. Verify types
    assert isinstance(found.due_date, date)
    assert isinstance(found.extracted_data, dict)

    # Cleanup
    if os.path.exists("test_bdis_sql.db"):
        os.remove("test_bdis_sql.db")


def test_repository_is_workspace_scoped():
    test_db = "sqlite:///:memory:"
    engine, session_factory = init_database(test_db)
    Base.metadata.create_all(engine)
    repo = SQLDocumentRepository(session_factory)

    ws_a = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    ws_b = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    extraction = DocumentExtraction(
        document_id="same-doc",
        status=JobStatus.VALIDATED,
        raw_text="Doc A",
        extracted_data={"company_name": "A"},
        money=Money(10.0, "USD"),
        company_name="A",
        due_date=date(2026, 4, 15),
        trace_id="trace-a",
        confidence=0.9,
    )

    extraction2 = DocumentExtraction(
        document_id="same-doc",
        status=JobStatus.VALIDATED,
        raw_text="Doc B",
        extracted_data={"company_name": "B"},
        money=Money(20.0, "USD"),
        company_name="B",
        due_date=date(2026, 4, 15),
        trace_id="trace-b",
        confidence=0.9,
    )

    repo.save(ws_a, extraction)
    repo.save(ws_b, extraction2)

    docs_a = repo.get_all_raw(ws_a)
    docs_b = repo.get_all_raw(ws_b)

    assert len(docs_a) == 1
    assert len(docs_b) == 1
    assert docs_a[0]["company_name"] == "A"
    assert docs_b[0]["company_name"] == "B"
