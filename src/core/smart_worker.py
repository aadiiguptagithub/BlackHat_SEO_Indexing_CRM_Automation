"""
Smart Worker with Auto-Shutdown
Automatically stops when no tasks are available
"""
import time
import random
import signal
import sys
import os
from datetime import datetime, timedelta
from .task_executor import execute_task
from src.client.api import api_client
from src.config import config
from src.utils.logging import logger

class SmartWorker:
    def __init__(self, idle_timeout_minutes=30, max_empty_polls=999999):
        self.running = True
        self.idle_timeout = timedelta(minutes=idle_timeout_minutes)
        self.max_empty_polls = max_empty_polls
        self.empty_poll_count = 0
        self.last_task_time = datetime.now()
        self.max_sleep_time = 300  # 5 minutes max sleep
        
        signal.signal(signal.SIGINT, self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)
    
    def _shutdown_handler(self, signum, frame):
        logger.info("Shutdown signal received")
        self.running = False
    
    def _should_shutdown(self):
        """Check if worker should shutdown due to inactivity"""
        idle_time = datetime.now() - self.last_task_time
        
        # Shutdown if idle for too long
        if idle_time > self.idle_timeout:
            logger.info(f"No tasks for {idle_time.total_seconds()/60:.1f} minutes. Shutting down to save resources.")
            return True
        
        # Shutdown if too many consecutive empty polls
        if self.empty_poll_count >= self.max_empty_polls:
            logger.info(f"No tasks found after {self.empty_poll_count} polls. Shutting down.")
            return True
        
        return False
    
    def run(self):
        """Main worker loop with smart shutdown"""
        logger.info("Smart Worker started")
        logger.info(f"Auto-shutdown after {self.idle_timeout.total_seconds()/60:.0f} minutes of inactivity")
        
        while self.running:
            try:
                # Claim task from API
                task_data = api_client.claim_task()
                
                if not task_data:
                    self.empty_poll_count += 1
                    
                    # Exponential backoff: 3s, 10s, 30s, 60s, 120s, 300s (5 min max)
                    if self.empty_poll_count <= 3:
                        sleep_time = 3 * self.empty_poll_count  # 3s, 6s, 9s
                    elif self.empty_poll_count <= 6:
                        sleep_time = 30  # 30s
                    elif self.empty_poll_count <= 10:
                        sleep_time = 60  # 1 min
                    elif self.empty_poll_count <= 15:
                        sleep_time = 120  # 2 min
                    else:
                        sleep_time = self.max_sleep_time  # 5 min
                    
                    logger.info(f"No tasks, sleeping {sleep_time}s (poll #{self.empty_poll_count})")
                    time.sleep(sleep_time)
                    continue
                
                # Reset counters when task found
                self.empty_poll_count = 0
                self.last_task_time = datetime.now()
                
                # Extract task info
                submission_id = task_data.get('_id')
                raw_job = task_data.get('jobId')
                job_id = raw_job.get('_id') if isinstance(raw_job, dict) else raw_job
                
                website = task_data.get('websiteId')
                url = website.get('url') if isinstance(website, dict) else website
                
                form_data = task_data.get('formData')
                if not form_data and isinstance(raw_job, dict):
                    form_data = raw_job.get('fields')
                
                task = {
                    'job_id': job_id,
                    'submission_id': submission_id,
                    'url': url,
                    'form_data': form_data
                }
                
                logger.info(f"Executing task {submission_id}")
                result = execute_task(task)
                
                # Report result
                if result['success']:
                    api_client.report_success(
                        submission_id, 
                        result['logs'], 
                        result['evidence']
                    )
                else:
                    api_client.report_failure(
                        submission_id,
                        result.get('error', 'Unknown error'),
                        result['logs']
                    )
                
                # Brief pause between tasks
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                time.sleep(5)
        
        logger.info("Smart Worker stopped - Resources saved!")

def start_smart_worker():
    """Start the smart worker"""
    worker = SmartWorker(
        idle_timeout_minutes=int(os.getenv('IDLE_TIMEOUT_MINUTES', '5')),
        max_empty_polls=int(os.getenv('MAX_EMPTY_POLLS', '10'))
    )
    worker.run()
