import pytest
import responses
import requests
from src.client.api import APIClient


@pytest.fixture
def api_client():
    return APIClient()


class TestAPIClient:
    
    @responses.activate
    def test_claim_task_returns_task_when_available(self, api_client):
        task_data = {
            'success': True,
            'data': {
                '_id': 'task123',
                'websiteId': {'url': 'https://example.com'}
            }
        }
        responses.add(
            responses.GET,
            f"{api_client.base_url}/submissions/next",
            json=task_data,
            status=200
        )
        
        result = api_client.claim_task()
        
        assert result == task_data['data']
    
    @responses.activate
    def test_claim_task_returns_none_when_no_tasks(self, api_client):
        responses.add(
            responses.GET,
            f"{api_client.base_url}/submissions/next",
            json={'success': False, 'data': None},
            status=200
        )
        
        result = api_client.claim_task()
        
        assert result is None
    
    @responses.activate
    def test_report_success_with_valid_data(self, api_client):
        responses.add(
            responses.PATCH,
            f"{api_client.base_url}/submissions/sub123",
            json={'success': True},
            status=200
        )
        
        result = api_client.report_success(
            'sub123',
            ['log1', 'log2'],
            {'screenshot': 'path/to/file'}
        )
        
        assert result is True
        assert len(responses.calls) == 1
        import json
        assert json.loads(responses.calls[0].request.body) == {
            'status': 'success',
            'logs': ['log1', 'log2'],
            'evidence': {'screenshot': 'path/to/file'}
        }
    
    @responses.activate
    def test_report_failure_with_error(self, api_client):
        responses.add(
            responses.PATCH,
            f"{api_client.base_url}/submissions/sub123",
            json={'success': True},
            status=200
        )
        
        result = api_client.report_failure('sub123', 'Test error', ['log1'])
        
        assert result is True
        import json
        assert json.loads(responses.calls[0].request.body) == {
            'status': 'failed',
            'error': 'Test error',
            'logs': ['log1']
        }
    
    @responses.activate
    def test_claim_task_network_error_handled(self, api_client):
        responses.add(
            responses.GET,
            f"{api_client.base_url}/submissions/next",
            body=requests.exceptions.ConnectionError()
        )
        
        result = api_client.claim_task()
        
        assert result is None
    
    @responses.activate
    def test_report_success_network_error_handled(self, api_client):
        responses.add(
            responses.PATCH,
            f"{api_client.base_url}/submissions/sub123",
            body=requests.exceptions.Timeout()
        )
        
        result = api_client.report_success('sub123', ['log1'])
        
        assert result is False
    
    @responses.activate
    def test_report_failure_network_error_handled(self, api_client):
        responses.add(
            responses.PATCH,
            f"{api_client.base_url}/submissions/sub123",
            status=500
        )
        
        result = api_client.report_failure('sub123', 'error', ['log1'])
        
        assert result is False