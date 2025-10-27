import pytest
import requests
import time
import os
import shutil
from pathlib import Path
from unittest.mock import patch
from src.core.worker import Worker
from src.core.task_executor import execute_task
from src.client.api import APIClient
from src.config import config


@pytest.fixture(scope="module")
def test_backend_url():
    """Backend URL for integration tests"""
    return os.getenv("TEST_API_BASE_URL", "http://localhost:4000/api")


@pytest.fixture(scope="module")
def test_api_client(test_backend_url):
    """API client configured for testing"""
    client = APIClient()
    client.base_url = test_backend_url
    return client


@pytest.fixture
def mock_website_server():
    """Mock website for form submission testing"""
    from http.server import HTTPServer, BaseHTTPRequestHandler
    import threading
    
    class MockHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            html = '''
            <html><body>
                <form method="POST" action="/submit">
                    <input name="email" type="email" required>
                    <input name="message" type="text" required>
                    <button type="submit">Submit</button>
                </form>
            </body></html>
            '''
            self.wfile.write(html.encode())
        
        def do_POST(self):
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body>Success!</body></html>')
        
        def log_message(self, format, *args):
            pass  # Suppress logs
    
    server = HTTPServer(('localhost', 8080), MockHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    
    yield "http://localhost:8080"
    server.shutdown()


@pytest.fixture
def test_evidence_dir():
    """Temporary evidence directory for testing"""
    test_dir = Path("./test_artifacts")
    test_dir.mkdir(exist_ok=True)
    
    # Patch config to use test directory
    original_dir = config.EVIDENCE_DIR
    config.EVIDENCE_DIR = str(test_dir)
    
    yield test_dir
    
    # Cleanup
    config.EVIDENCE_DIR = original_dir
    if test_dir.exists():
        shutil.rmtree(test_dir)


class TestIntegration:
    
    @pytest.mark.integration
    def test_full_workflow_with_real_backend(
        self, test_api_client, mock_website_server, test_evidence_dir
    ):
        """Test complete workflow: create job -> worker processes -> verify results"""
        
        # Skip if backend not available
        try:
            response = requests.get(f"{test_api_client.base_url}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Backend not available for integration test")
        except requests.exceptions.RequestException:
            pytest.skip("Backend not available for integration test")
        
        # 1. Create test job and submission
        job_data = self._create_test_job(test_api_client, mock_website_server)
        submission_data = self._create_test_submission(test_api_client, job_data['id'])
        
        try:
            # 2. Execute task directly (simulating worker)
            task = {
                'job_id': job_data['id'],
                'submission_id': submission_data['id'],
                'url': mock_website_server,
                'form_data': {
                    'email': 'test@example.com',
                    'message': 'Integration test message'
                }
            }
            
            result = execute_task(task)
            
            # 3. Verify task execution
            assert result['success'] is True
            assert len(result['logs']) > 0
            assert result['strategy'] in ['http', 'selenium']
            
            # 4. Report result to backend
            if result['success']:
                success = test_api_client.report_success(
                    submission_data['id'],
                    result['logs'],
                    result['evidence']
                )
                assert success is True
            
            # 5. Verify submission status updated
            submission_status = self._get_submission_status(
                test_api_client, submission_data['id']
            )
            assert submission_status == 'success'
            
            # 6. Verify evidence files created
            if result['evidence']:
                for evidence_type, file_path in result['evidence'].items():
                    assert Path(file_path).exists(), f"Evidence file missing: {file_path}"
            
        finally:
            # 7. Clean up test data
            self._cleanup_test_data(test_api_client, job_data['id'], submission_data['id'])
    
    @pytest.mark.integration
    def test_worker_integration_with_timeout(
        self, test_api_client, mock_website_server, test_evidence_dir
    ):
        """Test worker claims and processes task with timeout"""
        
        try:
            response = requests.get(f"{test_api_client.base_url}/health", timeout=5)
            if response.status_code != 200:
                pytest.skip("Backend not available for integration test")
        except requests.exceptions.RequestException:
            pytest.skip("Backend not available for integration test")
        
        # Create test data
        job_data = self._create_test_job(test_api_client, mock_website_server)
        submission_data = self._create_test_submission(test_api_client, job_data['id'])
        
        try:
            # Patch config for faster testing
            with patch.object(config, 'POLL_INTERVAL_MS', 500):
                worker = Worker()
                
                # Run worker for limited time
                start_time = time.time()
                timeout = 10  # 10 seconds max
                
                while time.time() - start_time < timeout:
                    # Check if task was processed
                    status = self._get_submission_status(test_api_client, submission_data['id'])
                    if status in ['success', 'failed']:
                        break
                    
                    # Simulate one worker iteration
                    task_data = test_api_client.claim_task()
                    if task_data and task_data['_id'] == submission_data['id']:
                        # Process the claimed task
                        task = {
                            'job_id': task_data['jobId'],
                            'submission_id': task_data['_id'],
                            'url': task_data['websiteId']['url'],
                            'form_data': task_data['formData']
                        }
                        
                        result = execute_task(task)
                        
                        if result['success']:
                            test_api_client.report_success(
                                task_data['_id'],
                                result['logs'],
                                result['evidence']
                            )
                        else:
                            test_api_client.report_failure(
                                task_data['_id'],
                                result.get('error', 'Unknown error'),
                                result['logs']
                            )
                        break
                    
                    time.sleep(0.5)
                
                # Verify final status
                final_status = self._get_submission_status(test_api_client, submission_data['id'])
                assert final_status in ['success', 'failed']
        
        finally:
            self._cleanup_test_data(test_api_client, job_data['id'], submission_data['id'])
    
    def _create_test_job(self, api_client, website_url):
        """Create test job via API"""
        job_payload = {
            'name': 'Integration Test Job',
            'website': {
                'url': website_url,
                'name': 'Test Site'
            }
        }
        
        response = requests.post(
            f"{api_client.base_url}/jobs",
            json=job_payload,
            headers=api_client.headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()['data']
    
    def _create_test_submission(self, api_client, job_id):
        """Create test submission via API"""
        submission_payload = {
            'jobId': job_id,
            'formData': {
                'email': 'test@example.com',
                'message': 'Integration test'
            }
        }
        
        response = requests.post(
            f"{api_client.base_url}/submissions",
            json=submission_payload,
            headers=api_client.headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()['data']
    
    def _get_submission_status(self, api_client, submission_id):
        """Get submission status from API"""
        response = requests.get(
            f"{api_client.base_url}/submissions/{submission_id}",
            headers=api_client.headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()['data']['status']
    
    def _cleanup_test_data(self, api_client, job_id, submission_id):
        """Clean up test data"""
        try:
            # Delete submission
            requests.delete(
                f"{api_client.base_url}/submissions/{submission_id}",
                headers=api_client.headers,
                timeout=10
            )
        except:
            pass
        
        try:
            # Delete job
            requests.delete(
                f"{api_client.base_url}/jobs/{job_id}",
                headers=api_client.headers,
                timeout=10
            )
        except:
            pass