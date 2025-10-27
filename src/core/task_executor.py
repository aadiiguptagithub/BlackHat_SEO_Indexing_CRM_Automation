import time
from src.drivers import get_driver
from .automation_runner import fill_and_submit
from .http_runner import submit_via_post
from .evidence import evidence_manager
from src.utils.logging import logger

def execute_task(task):
    """Execute submission task with strategy selection"""
    result = {
        'success': False,
        'strategy': None,
        'logs': [],
        'evidence': {},
        'error': None
    }
    
    try:
        job_id = task['job_id']
        submission_id = task['submission_id']
        url = task['url']
        form_data = task['form_data']
        
        result['logs'].append(f"Starting task {submission_id} for job {job_id}")
        
        # Try HTTP POST first (faster)
        result['strategy'] = 'http'
        http_result = submit_via_post(url, form_data)
        
        if http_result['success']:
            result['success'] = True
            result['logs'].extend([f"HTTP POST successful - Status: {http_result['status_code']}"])
            
            # Save response HTML
            if http_result['response_html']:
                html_path = evidence_manager.save_html(
                    job_id, submission_id, http_result['response_html'], 'response.html'
                )
                if html_path:
                    result['evidence']['htmlPath'] = html_path
        else:
            # Fallback to Selenium
            result['strategy'] = 'selenium'
            result['logs'].append(f"HTTP failed: {http_result.get('error', 'Unknown error')}, trying Selenium")
            
            driver = None
            try:
                driver = get_driver()
                selenium_result = fill_and_submit(driver, url, form_data)
                
                result['success'] = selenium_result['success']
                result['logs'].extend(selenium_result['logs'])
                
                # Save screenshots
                if selenium_result['screenshots']['before']:
                    before_path = evidence_manager.save_screenshot(
                        job_id, submission_id, selenium_result['screenshots']['before'], 'before.png'
                    )
                    if before_path:
                        result['evidence']['screenshotPath'] = before_path
                
                if selenium_result['screenshots']['after']:
                    after_path = evidence_manager.save_screenshot(
                        job_id, submission_id, selenium_result['screenshots']['after'], 'after.png'
                    )
                    if after_path:
                        result['evidence']['screenshotPath'] = after_path
                
                # Save page HTML
                try:
                    page_html = driver.page_source
                    html_path = evidence_manager.save_html(
                        job_id, submission_id, page_html, 'page.html'
                    )
                    if html_path:
                        result['evidence']['htmlPath'] = html_path
                except:
                    pass
                
                if not selenium_result['success']:
                    result['error'] = selenium_result.get('error', 'Selenium execution failed')
                    
            finally:
                if driver:
                    driver.quit()
        
        if result['success']:
            result['logs'].append(f"Task completed successfully using {result['strategy']}")
        else:
            result['logs'].append(f"Task failed with {result['strategy']} strategy")
            
    except Exception as e:
        result['error'] = str(e)
        result['logs'].append(f"Execution error: {e}")
        logger.error(f"Task execution failed: {e}")
    
    return result