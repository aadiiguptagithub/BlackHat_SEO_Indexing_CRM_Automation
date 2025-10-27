import requests
from typing import Optional, Dict, Any
from src.config import config
from src.utils.logging import logger

class APIClient:
    """Client for backend API communication"""
    
    def __init__(self):
        self.base_url = config.API_BASE_URL
        self.api_key = config.WORKER_API_KEY
        self.headers = {
            'x-api-key': self.api_key,
            'Content-Type': 'application/json'
        }
    
    def claim_task(self, lease_seconds: int = None) -> Optional[Dict[str, Any]]:
        """Claim next available submission"""
        try:
            lease = lease_seconds or config.LEASE_SECONDS
            url = f"{self.base_url}/submissions/next?lease={lease}"
            
            logger.info(f"Claiming task with lease={lease}s")
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('success') and data.get('data'):
                task = data['data']
                logger.info(f"Task claimed: {task.get('_id')} - {task.get('websiteId', {}).get('url')}")
                return task
            else:
                logger.info("No tasks available")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to claim task: {e}")
            return None
    
    def report_success(
        self, 
        submission_id: str, 
        logs: list, 
        evidence: Dict[str, str] = None
    ) -> bool:
        """Report successful submission"""
        try:
            url = f"{self.base_url}/submissions/{submission_id}"
            
            payload = {
                'status': 'success',
                'logs': logs,
                'evidence': evidence or {}
            }
            
            logger.info(f"Reporting success for {submission_id}")
            response = requests.patch(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Success reported for {submission_id}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to report success: {e}")
            return False
    
    def report_failure(
        self, 
        submission_id: str, 
        error: str, 
        logs: list
    ) -> bool:
        """Report failed submission"""
        try:
            url = f"{self.base_url}/submissions/{submission_id}"
            
            payload = {
                'status': 'failed',
                'error': error,
                'logs': logs
            }
            
            logger.info(f"Reporting failure for {submission_id}")
            response = requests.patch(url, json=payload, headers=self.headers, timeout=10)
            response.raise_for_status()
            
            logger.info(f"Failure reported for {submission_id}: {error}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to report failure: {e}")
            return False

# Global instance
api_client = APIClient()
