import os
from datetime import datetime
from src.config import config
from src.utils.logging import logger

class EvidenceManager:
    """Manage evidence files (screenshots, HTML)"""
    
    def __init__(self):
        self.base_dir = config.EVIDENCE_DIR
    
    def get_submission_dir(self, job_id: str, submission_id: str) -> str:
        """Get directory path for a submission"""
        path = os.path.join(self.base_dir, job_id, submission_id)
        os.makedirs(path, exist_ok=True)
        return path
    
    def save_screenshot(
        self, 
        job_id: str, 
        submission_id: str, 
        screenshot_data: bytes, 
        filename: str = None
    ) -> str:
        """Save screenshot and return relative path"""
        try:
            submission_dir = self.get_submission_dir(job_id, submission_id)
            
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'screenshot_{timestamp}.png'
            
            filepath = os.path.join(submission_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(screenshot_data)
            
            # Return relative path
            relative_path = os.path.join(job_id, submission_id, filename)
            logger.info(f"Screenshot saved: {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"Failed to save screenshot: {e}")
            return None
    
    def save_html(
        self, 
        job_id: str, 
        submission_id: str, 
        html_content: str, 
        filename: str = None
    ) -> str:
        """Save HTML and return relative path"""
        try:
            submission_dir = self.get_submission_dir(job_id, submission_id)
            
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'page_{timestamp}.html'
            
            filepath = os.path.join(submission_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Return relative path
            relative_path = os.path.join(job_id, submission_id, filename)
            logger.info(f"HTML saved: {relative_path}")
            return relative_path
            
        except Exception as e:
            logger.error(f"Failed to save HTML: {e}")
            return None

# Global instance
evidence_manager = EvidenceManager()
