#!/usr/bin/env python3
"""
Black Hat SEO Automation Worker
"""

import signal
import sys
import os
from src.config import config
from src.utils.logging import logger

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

def print_banner():
    """Print startup banner with config"""
    logger.info("="*50)
    logger.info("Black Hat SEO Automation Worker")
    logger.info("="*50)
    logger.info(f"API URL: {config.API_BASE_URL}")
    logger.info(f"Driver: {config.DRIVER}")
    logger.info(f"Headless: {config.HEADLESS}")
    logger.info(f"Poll Interval: {config.POLL_INTERVAL_MS}ms")
    logger.info(f"Evidence Dir: {config.EVIDENCE_DIR}")
    logger.info("="*50)

def main():
    """Main entry point"""
    try:
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Validate configuration
        config.validate()
        
        # Print startup banner
        print_banner()
        
        # Check if smart worker is enabled
        use_smart_worker = os.getenv('USE_SMART_WORKER', 'true').lower() == 'true'
        
        if use_smart_worker:
            logger.info("Starting Smart Worker (auto-shutdown enabled)")
            from src.core.smart_worker import start_smart_worker
            start_smart_worker()
        else:
            logger.info("Starting Standard Worker (continuous mode)")
            from src.core import start_worker
            start_worker()
        
    except KeyboardInterrupt:
        logger.info("Worker shutdown complete")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())