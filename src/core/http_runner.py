import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from src.utils.logging import logger

def submit_via_post(url, form_data):
    """Submit form data via HTTP POST"""
    result = {
        'success': False,
        'response_html': None,
        'status_code': None,
        'error': None
    }
    
    try:
        # Get page to detect form action
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find form action URL
        form = soup.find('form')
        if not form:
            result['error'] = "No form found"
            return result
        
        action = form.get('action', '')
        if not action:
            action_url = url
        elif action.startswith('http'):
            action_url = action
        else:
            action_url = urljoin(url, action)
        
        # Submit form data
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': url
        }
        
        post_response = requests.post(action_url, data=form_data, headers=headers, timeout=10)
        
        result['status_code'] = post_response.status_code
        result['response_html'] = post_response.text
        result['success'] = 200 <= post_response.status_code < 400
        
        logger.info(f"POST to {action_url} - Status: {post_response.status_code}")
        
    except requests.RequestException as e:
        result['error'] = str(e)
        logger.error(f"HTTP POST failed: {e}")
    
    return result