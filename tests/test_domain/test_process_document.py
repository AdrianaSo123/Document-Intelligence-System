from datetime import date, timedelta
import pytest

from bdis.domain.entities import DocumentInsight
from bdis.ports.extraction_service import IExtractionService
from bdis.ports.document_repository import IDocumentRepository
from bdis.usecases.process_document import ProcessDocumentUseCase

class MockExtractionService(IExtractionService):
    def __init__(self, mock_response: dict):
        self.mock_response = mock_response

    def extract_schema(self, raw_text: str) -> dict:
        return self.mock_response

class MockDocumentRepository(IDocumentRepository):
    def __init__(self):
        self.saved_insights = []

    def save(self, insight: DocumentInsight) -> str:
        self.saved_insights.append(insight)
        return f"mock_id_{len(self.saved_insights)}"

    def get_all(self):
        return self.saved_insights
        
    def get_all_raw(self):
        return [
            {
                "document_id": f"mock_id_{i}",
                "company_name": insight.company_name,
                "amount_usd": insight.amount_usd,
                "status": insight.status,
                "due_date": insight.due_date
            }
            for i, insight in enumerate(self.saved_insights)
        ]

def test_document_insight_risk_rules():
    # 1. High Amount Risk
    insight = DocumentInsight(amount_usd=15000, status="paid", due_date=date.today(), company_name="Acme Corp")
    assert insight.calculate_risk_flag() is True

    # 2. Unpaid & Overdue Risk
    thirty_one_days_ago = date.today() - timedelta(days=31)
    insight2 = DocumentInsight(amount_usd=500, status="unpaid", due_date=thirty_one_days_ago, company_name="Acme Corp")
    assert insight2.calculate_risk_flag() is True

    # 3. Missing Company Name Risk
    insight3 = DocumentInsight(amount_usd=500, status="paid", due_date=date.today(), company_name="")
    assert insight3.calculate_risk_flag() is True

    # 4. Healthy Document
    insight4 = DocumentInsight(amount_usd=500, status="paid", due_date=date.today(), company_name="Acme Corp")
    assert insight4.calculate_risk_flag() is False

def test_process_document_usecase_orchestration():
    mock_data = {
        "company_name": "Stripe Inc.",
        "amount_usd": 1200.0,
        "due_date": "2026-04-01",
        "status": "unpaid"
    }
    
    extractor = MockExtractionService(mock_data)
    repo = MockDocumentRepository()
    
    usecase = ProcessDocumentUseCase(extractor, repo)
    
    # Execute workflow
    result_id = usecase.execute("fake raw pdf text")
    
    # Verify outputs
    assert result_id == "mock_id_1"
    assert len(repo.saved_insights) == 1
    
    saved_entity = repo.saved_insights[0]
    assert saved_entity.company_name == "Stripe Inc."
    assert saved_entity.amount_usd == 1200.0
    assert saved_entity.due_date == date.fromisoformat("2026-04-01")
    assert saved_entity.status == "unpaid"
