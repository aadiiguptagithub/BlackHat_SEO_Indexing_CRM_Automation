import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Configuration from environment variables"""
    
    # API Configuration
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:3000/api')
    WORKER_API_KEY = os.getenv('WORKER_API_KEY', '')
    
    # Driver Configuration
    DRIVER = os.getenv('DRIVER', 'chrome')
    HEADLESS = os.getenv('HEADLESS', 'true').lower() == 'true'
    
    # Evidence Storage
    EVIDENCE_DIR = os.getenv('EVIDENCE_DIR', './artifacts')
    
    # Worker Configuration
    POLL_INTERVAL_MS = int(os.getenv('POLL_INTERVAL_MS', '2000'))
    CLAIM_BATCH_SIZE = int(os.getenv('CLAIM_BATCH_SIZE', '1'))
    LEASE_SECONDS = int(os.getenv('LEASE_SECONDS', '120'))
    MAX_ATTEMPTS = int(os.getenv('MAX_ATTEMPTS', '3'))
    
    # Timing Configuration
    MIN_DELAY = float(os.getenv('MIN_DELAY', '2'))
    MAX_DELAY = float(os.getenv('MAX_DELAY', '5'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './logs/worker.log')
    
    # Proxy Configuration
    USE_PROXY = os.getenv('USE_PROXY', 'false').lower() == 'true'
    PROXY_LIST = os.getenv('PROXY_LIST', '').split(',') if os.getenv('PROXY_LIST') else []
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.WORKER_API_KEY:
            raise ValueError("WORKER_API_KEY is required in .env file")
        
        if not cls.API_BASE_URL:
            raise ValueError("API_BASE_URL is required in .env file")
        
        # Create directories if they don't exist
        os.makedirs(cls.EVIDENCE_DIR, exist_ok=True)
        os.makedirs(os.path.dirname(cls.LOG_FILE), exist_ok=True)

config = Config()
