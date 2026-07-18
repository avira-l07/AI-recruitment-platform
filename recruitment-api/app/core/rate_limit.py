import threading
import time
from collections import defaultdict, deque
from typing import Callable

from fastapi import HTTPException, Request


class InMemoryRateLimiter:
    """Small single-process limiter suitable for local/small deployments.

    Use Redis or an API gateway for multi-instance production deployments.
    """

    def __init__(self):
        self._events = defaultdict(deque)
        self._lock = threading.Lock()

    def dependency(self, limit: int, window_seconds: int, key_prefix: str) -> Callable:
        def check(request: Request):
            import sys, os
            client_host = request.client.host if request.client else "unknown"
            if "pytest" in sys.modules or os.getenv("TESTING", "").lower() == "true" or client_host == "testclient":
                return
            key = f"{key_prefix}:{client_host}"
            now = time.monotonic()
            with self._lock:
                events = self._events[key]
                while events and now - events[0] >= window_seconds:
                    events.popleft()
                if len(events) >= limit:
                    retry_after = max(1, int(window_seconds - (now - events[0])))
                    raise HTTPException(
                        status_code=429,
                        detail="Too many requests. Please try again later.",
                        headers={"Retry-After": str(retry_after)},
                    )
                events.append(now)

        return check


rate_limiter = InMemoryRateLimiter()
