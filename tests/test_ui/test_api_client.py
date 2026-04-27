from unittest.mock import patch, Mock
import pytest
import requests
from bdis.frameworks.ui.api_client import BdisApiClient
from bdis.frameworks.ui.view_models import DashboardViewModel, ErrorViewModel

@patch('requests.get')
def test_api_client_graceful_network_degradation(mock_get):
    """Proves the UI won't crash if the backend container is offline"""
    mock_get.side_effect = requests.exceptions.ConnectionError("Network Down")
    
    client = BdisApiClient()
    result = client.fetch_all_documents()
    
    assert isinstance(result, ErrorViewModel)
    assert result.is_error is True
    assert "offline" in result.error_message

@patch('requests.get')
def test_api_client_json_mapping(mock_get):
    """Proves raw JSON safely maps to rigid DTOs"""
    fake_response = Mock()
    fake_response.json.return_value = [
        {"document_id": "1", "company_name": "TestCorp", "amount_usd": 15000, "status": "unpaid", "is_high_risk": True}
    ]
    mock_get.return_value = fake_response
    
    client = BdisApiClient()
    result = client.fetch_all_documents()
    
    assert isinstance(result, list)
    assert isinstance(result[0], DashboardViewModel)
    assert result[0].company_name == "TestCorp"
    assert result[0].is_high_risk is True # $15,000 + unpaid = high risk True
