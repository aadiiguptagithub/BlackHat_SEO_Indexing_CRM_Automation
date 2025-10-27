import time
import random
import signal
import sys
from .task_executor import execute_task
from src.client.api import api_client
from src.config import config
from src.utils.logging import logger

class Worker:
    def __init__(self):
        self.running = True
        signal.signal(signal.SIGINT, self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)
    
    def _shutdown_handler(self, signum, frame):
        logger.info("Shutdown signal received, stopping worker...")
        self.running = False
    
    def run(self):
        """Main worker loop"""
        logger.info("Worker started")
        
        while self.running:
            try:
                # Claim task from API
                task_data = api_client.claim_task()
                
                if not task_data:
                    # No tasks available, sleep with jitter
                    sleep_time = config.POLL_INTERVAL_MS / 1000 + random.uniform(0, 1)
                    logger.debug(f"No tasks, sleeping {sleep_time:.1f}s")
                    time.sleep(sleep_time)
                    continue
                
                # Extract task info (support multiple task shapes)
                submission_id = task_data.get('_id')

                # jobId in task_data can be an object or a string id
                raw_job = task_data.get('jobId')
                if isinstance(raw_job, dict):
                    job_id = raw_job.get('_id') or raw_job.get('id')
                else:
                    job_id = raw_job

                # websiteId may be an object with url or a string
                website = task_data.get('websiteId')
                if isinstance(website, dict):
                    url = website.get('url')
                else:
                    url = website

                # form data may come as top-level 'formData' or inside job object
                if 'formData' in task_data:
                    form_data = task_data.get('formData')
                elif isinstance(raw_job, dict):
                    form_data = raw_job.get('fields')
                else:
                    form_data = None
                
                # Execute task
                task = {
                    'job_id': job_id,
                    'submission_id': submission_id,
                    'url': url,
                    'form_data': form_data
                }
                
                logger.info(f"Executing task {submission_id}")
                result = execute_task(task)
                
                # Report result to API
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
                time.sleep(random.uniform(1, 3))
                
            except Exception as e:
                logger.error(f"Worker loop error: {e}")
                time.sleep(5)  # Longer pause on error
        
        logger.info("Worker stopped")

def start_worker():
    """Start the worker"""
    worker = Worker()
    worker.run()