import time
from app.ai.api_errors import AIRateLimitError


class RateLimitManager:
    def __init__(self, max_retries=3, minimum_interval=0.15, sleep=time.sleep): self.max_retries=max(0,int(max_retries)); self.minimum_interval=minimum_interval; self.sleep=sleep; self._last=0.0
    def run(self, operation, on_wait=None):
        for attempt in range(self.max_retries+1):
            elapsed=time.monotonic()-self._last
            if elapsed < self.minimum_interval: self.sleep(self.minimum_interval-elapsed)
            try:
                result=operation(); self._last=time.monotonic(); return result
            except AIRateLimitError as error:
                if attempt>=self.max_retries: raise
                delay=max(error.retry_after, min(30.0, 2**attempt))
                if on_wait: on_wait(delay, attempt+1)
                self.sleep(delay)
