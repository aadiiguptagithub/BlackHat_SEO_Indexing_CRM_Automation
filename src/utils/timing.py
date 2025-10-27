import time
import random
from src.config import config

def random_delay(min_seconds: float = None, max_seconds: float = None):
    """Sleep for a random duration to mimic human behavior"""
    min_delay = min_seconds or config.MIN_DELAY
    max_delay = max_seconds or config.MAX_DELAY
    
    delay = random.uniform(min_delay, max_delay)
    time.sleep(delay)
    return delay

def jitter_sleep(base_seconds: float, jitter_percent: float = 0.2):
    """Sleep with jitter"""
    jitter = base_seconds * jitter_percent
    delay = base_seconds + random.uniform(-jitter, jitter)
    time.sleep(max(0, delay))
    return delay
