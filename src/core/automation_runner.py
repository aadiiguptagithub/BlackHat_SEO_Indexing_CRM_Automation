import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .form_detector import detect_form_fields
from src.utils.logging import logger

def fill_and_submit(driver, url, fields_data):
    """Fill form and submit with automation detection"""
    result = {
        'success': False,
        'logs': [],
        'screenshots': {'before': None, 'after': None},
        'error': None
    }
    
    try:
        # Navigate to URL
        driver.get(url)
        result['logs'].append(f"Navigated to {url}")
        
        # Wait for page load
        WebDriverWait(driver, 10).until(
            lambda d: d.execute_script("return document.readyState") == "complete"
        )
        
        # Take before screenshot
        result['screenshots']['before'] = driver.get_screenshot_as_png()
        result['logs'].append("Before screenshot taken")
        
        # Detect CAPTCHA
        if _has_captcha(driver):
            result['error'] = "CAPTCHA detected"
            result['logs'].append("CAPTCHA found - marking as failed")
            return result
        
        # Detect form fields
        html = driver.page_source
        forms = detect_form_fields(html)
        
        if not forms['forms']:
            result['error'] = "No forms detected"
            result['logs'].append("No forms found on page")
            return result
        
        # Fill first form with detected fields
        form_data = forms['forms'][0]
        filled_count = 0
        
        for field_type, field_info in form_data['fields'].items():
            if field_type in fields_data:
                try:
                    element = driver.find_element(By.CSS_SELECTOR, field_info['selector'])
                    _human_type(element, fields_data[field_type])
                    filled_count += 1
                    result['logs'].append(f"Filled {field_type} field")
                except NoSuchElementException:
                    result['logs'].append(f"Field {field_type} not found")
        
        if filled_count == 0:
            result['error'] = "No matching fields found"
            result['logs'].append("No fields could be filled")
            return result
        
        # Submit form
        submit_btn = driver.find_element(By.CSS_SELECTOR, "input[type='submit'], button[type='submit'], button:contains('Submit')")
        submit_btn.click()
        result['logs'].append("Form submitted")
        
        # Wait for response
        time.sleep(2)
        
        # Take after screenshot
        result['screenshots']['after'] = driver.get_screenshot_as_png()
        result['logs'].append("After screenshot taken")
        
        result['success'] = True
        result['logs'].append("Automation completed successfully")
        
    except TimeoutException:
        result['error'] = "Page load timeout"
        result['logs'].append("Timeout waiting for page")
    except Exception as e:
        result['error'] = str(e)
        result['logs'].append(f"Error: {e}")
    
    return result

def _has_captcha(driver):
    """Check for CAPTCHA presence"""
    captcha_selectors = [
        "[class*='captcha']", "[id*='captcha']",
        "[class*='recaptcha']", "[id*='recaptcha']",
        "iframe[src*='recaptcha']", ".g-recaptcha"
    ]
    
    for selector in captcha_selectors:
        try:
            driver.find_element(By.CSS_SELECTOR, selector)
            return True
        except NoSuchElementException:
            continue
    return False

def _human_type(element, text):
    """Type with human-like delays"""
    element.clear()
    for char in text:
        element.send_keys(char)
        time.sleep(random.uniform(0.05, 0.15))