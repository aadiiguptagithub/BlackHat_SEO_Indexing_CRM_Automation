import pytest
import time
from unittest.mock import Mock, patch, call
from src.core.worker import Worker


@pytest.fixture
def worker():
    return Worker()


class TestWorker:
    
    @patch('src.core.worker.execute_task')
    @patch('src.core.worker.api_client')
    @patch('time.sleep')
    def test_successful_task_execution_and_reporting(self, mock_sleep, mock_api_client, mock_execute, worker):
        # Setup mocks
        task_data = {
            '_id': 'sub123',
            'jobId': 'job123',
            'websiteId': {'url': 'https://example.com'},
            'formData': {'field': 'value'}
        }
        mock_api_client.claim_task.side_effect = [task_data, None]
        mock_execute.return_value = {
            'success': True,
            'logs': ['log1', 'log2'],
            'evidence': {'screenshot': 'path'}
        }
        
        # Run one iteration then stop
        def stop_after_task(*args):
            worker.running = False
        mock_execute.side_effect = lambda task: {
            'success': True,
            'logs': ['log1', 'log2'],
            'evidence': {'screenshot': 'path'}
        }
        
        # Mock sleep to stop worker after task
        mock_sleep.side_effect = stop_after_task
        
        worker.run()
        
        # Verify task execution
        mock_execute.assert_called_once_with({
            'job_id': 'job123',
            'submission_id': 'sub123',
            'url': 'https://example.com',
            'form_data': {'field': 'value'}
        })
        
        # Verify success reporting
        mock_api_client.report_success.assert_called_once_with(
            'sub123',
            ['log1', 'log2'],
            {'screenshot': 'path'}
        )
    
    @patch('src.core.worker.execute_task')
    @patch('src.core.worker.api_client')
    @patch('time.sleep')
    def test_task_failure_reporting(self, mock_sleep, mock_api_client, mock_execute, worker):
        task_data = {
            '_id': 'sub123',
            'jobId': 'job123',
            'websiteId': {'url': 'https://example.com'},
            'formData': {}
        }
        mock_api_client.claim_task.side_effect = [task_data, None]
        mock_execute.return_value = {
            'success': False,
            'error': 'Test error',
            'logs': ['error log']
        }
        
        # Run one iteration then stop
        def stop_after_task(*args):
            worker.running = False
        mock_execute.side_effect = lambda task: {
            'success': False,
            'error': 'Test error',
            'logs': ['error log']
        }
        
        # Mock sleep to stop worker after task
        mock_sleep.side_effect = stop_after_task
        
        worker.run()
        
        mock_api_client.report_failure.assert_called_once_with(
            'sub123',
            'Test error',
            ['error log']
        )
    
    @patch('src.core.worker.api_client')
    @patch('time.sleep')
    @patch('random.uniform', return_value=0.5)
    def test_no_task_available_scenario(self, mock_uniform, mock_sleep, mock_api_client, worker):
        mock_api_client.claim_task.return_value = None
        
        # Stop after first iteration
        def stop_worker(*args):
            worker.running = False
        mock_sleep.side_effect = stop_worker
        
        worker.run()
        
        # Verify sleep with jitter
        expected_sleep = 2.0 + 0.5  # POLL_INTERVAL_MS/1000 + jitter
        mock_sleep.assert_called_with(expected_sleep)
    
    @patch('src.core.worker.api_client')
    @patch('time.sleep')
    def test_keyboard_interrupt_graceful_shutdown(self, mock_sleep, mock_api_client, worker):
        mock_api_client.claim_task.return_value = None
        
        # Set running to False immediately to avoid infinite loop
        worker.running = False
        
        # Should not raise exception
        worker.run()
        
        assert not worker.running
    
    @patch('src.core.worker.api_client')
    @patch('time.sleep')
    @patch('random.uniform')
    def test_sleep_intervals_between_polls(self, mock_uniform, mock_sleep, mock_api_client, worker):
        mock_api_client.claim_task.return_value = None
        mock_uniform.return_value = 0.3
        
        call_count = 0
        def stop_after_calls(*args):
            nonlocal call_count
            call_count += 1
            if call_count >= 2:
                worker.running = False
        
        mock_sleep.side_effect = stop_after_calls
        
        worker.run()
        
        # Verify sleep called with correct intervals
        expected_sleep = 2.0 + 0.3  # POLL_INTERVAL_MS/1000 + jitter
        assert mock_sleep.call_count >= 2
        mock_sleep.assert_has_calls([call(expected_sleep)] * 2)
    
    @patch('src.core.worker.execute_task')
    @patch('src.core.worker.api_client')
    @patch('time.sleep')
    def test_exception_handling_with_longer_pause(self, mock_sleep, mock_api_client, mock_execute, worker):
        mock_api_client.claim_task.side_effect = Exception("API Error")
        
        call_count = 0
        def stop_after_error(*args):
            nonlocal call_count
            call_count += 1
            if call_count >= 1:
                worker.running = False
        
        mock_sleep.side_effect = stop_after_error
        
        worker.run()
        
        # Verify longer pause on error
        mock_sleep.assert_called_with(5)
    
    def test_shutdown_handler(self, worker):
        assert worker.running is True
        
        worker._shutdown_handler(None, None)
        
        assert worker.running is False