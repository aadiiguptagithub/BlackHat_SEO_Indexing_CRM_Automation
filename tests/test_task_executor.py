import pytest
from unittest.mock import Mock, patch, MagicMock
from src.core.task_executor import execute_task


@pytest.fixture
def sample_task():
    return {
        'job_id': 'job123',
        'submission_id': 'sub123',
        'url': 'https://example.com',
        'form_data': {'field': 'value'}
    }


class TestTaskExecutor:
    
    @patch('src.core.task_executor.evidence_manager')
    @patch('src.core.task_executor.get_driver')
    @patch('src.core.task_executor.fill_and_submit')
    @patch('src.core.task_executor.submit_via_post')
    def test_execute_returns_success_with_logs_and_evidence_http(
        self, mock_post, mock_selenium, mock_driver, mock_evidence, sample_task
    ):
        # Mock HTTP success
        mock_post.return_value = {
            'success': True,
            'status_code': 200,
            'response_html': '<html>response</html>'
        }
        mock_evidence.save_html.return_value = '/path/to/response.html'
        
        result = execute_task(sample_task)
        
        assert result['success'] is True
        assert result['strategy'] == 'http'
        assert 'HTTP POST successful' in result['logs'][1]
        assert result['evidence']['response_html'] == '/path/to/response.html'
        mock_evidence.save_html.assert_called_once_with(
            'job123', 'sub123', '<html>response</html>', 'response.html'
        )
    
    @patch('src.core.task_executor.evidence_manager')
    @patch('src.core.task_executor.get_driver')
    @patch('src.core.task_executor.fill_and_submit')
    @patch('src.core.task_executor.submit_via_post')
    def test_execute_returns_success_with_selenium_fallback(
        self, mock_post, mock_selenium, mock_driver, mock_evidence, sample_task
    ):
        # Mock HTTP failure, Selenium success
        mock_post.return_value = {'success': False, 'error': 'HTTP failed'}
        mock_driver_instance = Mock()
        mock_driver_instance.page_source = '<html>page</html>'
        mock_driver.return_value = mock_driver_instance
        
        mock_selenium.return_value = {
            'success': True,
            'logs': ['Selenium log'],
            'screenshots': {
                'before': b'before_data',
                'after': b'after_data'
            }
        }
        
        mock_evidence.save_screenshot.side_effect = ['/path/before.png', '/path/after.png']
        mock_evidence.save_html.return_value = '/path/page.html'
        
        result = execute_task(sample_task)
        
        assert result['success'] is True
        assert result['strategy'] == 'selenium'
        assert result['evidence']['before_screenshot'] == '/path/before.png'
        assert result['evidence']['after_screenshot'] == '/path/after.png'
        assert result['evidence']['page_html'] == '/path/page.html'
    
    @patch('src.core.task_executor.evidence_manager')
    @patch('src.core.task_executor.get_driver')
    @patch('src.core.task_executor.fill_and_submit')
    @patch('src.core.task_executor.submit_via_post')
    def test_evidence_manager_called_with_correct_paths(
        self, mock_post, mock_selenium, mock_driver, mock_evidence, sample_task
    ):
        mock_post.return_value = {'success': False}
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        mock_selenium.return_value = {
            'success': True,
            'logs': [],
            'screenshots': {'before': b'data', 'after': None}
        }
        
        execute_task(sample_task)
        
        mock_evidence.save_screenshot.assert_called_once_with(
            'job123', 'sub123', b'data', 'before.png'
        )
    
    @patch('src.core.task_executor.evidence_manager')
    @patch('src.core.task_executor.get_driver')
    @patch('src.core.task_executor.fill_and_submit')
    @patch('src.core.task_executor.submit_via_post')
    def test_driver_cleanup_on_completion(
        self, mock_post, mock_selenium, mock_driver, mock_evidence, sample_task
    ):
        mock_post.return_value = {'success': False}
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        mock_selenium.return_value = {
            'success': True,
            'logs': [],
            'screenshots': {'before': None, 'after': None}
        }
        
        execute_task(sample_task)
        
        mock_driver_instance.quit.assert_called_once()
    
    @patch('src.core.task_executor.evidence_manager')
    @patch('src.core.task_executor.get_driver')
    @patch('src.core.task_executor.fill_and_submit')
    @patch('src.core.task_executor.submit_via_post')
    def test_driver_cleanup_on_exception(
        self, mock_post, mock_selenium, mock_driver, mock_evidence, sample_task
    ):
        mock_post.return_value = {'success': False}
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        mock_selenium.side_effect = Exception("Selenium error")
        
        result = execute_task(sample_task)
        
        mock_driver_instance.quit.assert_called_once()
        assert result['success'] is False
        assert result['error'] == "Selenium error"
    
    @patch('src.core.task_executor.evidence_manager')
    @patch('src.core.task_executor.get_driver')
    @patch('src.core.task_executor.fill_and_submit')
    @patch('src.core.task_executor.submit_via_post')
    def test_error_handling_and_failure_reporting(
        self, mock_post, mock_selenium, mock_driver, mock_evidence, sample_task
    ):
        mock_post.return_value = {'success': False, 'error': 'HTTP error'}
        mock_driver_instance = Mock()
        mock_driver.return_value = mock_driver_instance
        
        mock_selenium.return_value = {
            'success': False,
            'error': 'Form not found',
            'logs': ['Error log'],
            'screenshots': {'before': None, 'after': None}
        }
        
        result = execute_task(sample_task)
        
        assert result['success'] is False
        assert result['error'] == 'Form not found'
        assert result['strategy'] == 'selenium'
        assert 'HTTP failed: HTTP error' in result['logs'][1]
    
    @patch('src.core.task_executor.submit_via_post')
    def test_exception_handling_in_main_execution(self, mock_post, sample_task):
        mock_post.side_effect = Exception("Unexpected error")
        
        result = execute_task(sample_task)
        
        assert result['success'] is False
        assert result['error'] == "Unexpected error"
        assert "Execution error: Unexpected error" in result['logs']