import os
import pytest
from datetime import date
from bdis.domain.entities import DocumentInsight
from bdis.adapters.repositories import SqliteDocumentRepository, DocumentInsightModel

def test_sqlite_repository_save_and_retrieve():
    test_db = "sqlite:///test_bdis_integration.db"
    repo = SqliteDocumentRepository(test_db)
    
    insight = DocumentInsight(
        amount_usd=150.75,
        status="paid",
        due_date=date(2026, 4, 15),
        company_name="Integration Test Corp"
    )
    
    # Text Save
    saved_id = repo.save(insight)
    assert saved_id is not None
    assert type(saved_id) is str
    
    # Verify by reading directly via sqlalchemy
    with repo.SessionLocal() as session:
        fetched = session.query(DocumentInsightModel).filter_by(id=saved_id).first()
        assert fetched is not None
        assert fetched.company_name == "Integration Test Corp"
        assert fetched.amount_usd == 150.75
        
    # Cleanup
    if os.path.exists("test_bdis_integration.db"):
        os.remove("test_bdis_integration.db")
