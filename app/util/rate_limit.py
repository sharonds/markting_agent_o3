
import time, random, threading
from typing import Callable, Any

class RateLimiter:
    def __init__(self, max_concurrency: int = 4):
        self.sem = threading.Semaphore(max_concurrency)

    def call(self, fn: Callable[[], Any], retries: int = 3, base_delay: float = 0.5) -> Any:
        with self.sem:
            attempt = 0
            while True:
                try:
                    return fn()
                except Exception as e:
                    attempt += 1
                    if attempt > retries:
                        raise
                    time.sleep(base_delay * (2 ** (attempt - 1)) + random.random() * 0.2)
