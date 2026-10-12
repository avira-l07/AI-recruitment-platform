import threading
import time
import math
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
        self._expires = {}
        self._next_cleanup = 0.0

    def dependency(self, limit: int, window_seconds: int, key_prefix: str) -> Callable:
        def check(request: Request):
            client_host = request.client.host if request.client else "unknown"
            key = f"{key_prefix}:{client_host}"
            now = time.monotonic()
            with self._lock:
                if now >= self._next_cleanup:
                    for old_key in list(self._events):
                        if self._expires.get(old_key, 0) <= now:
                            self._events.pop(old_key, None)
                            self._expires.pop(old_key, None)
                    self._next_cleanup = now + 60
                events = self._events[key]
                while events and now - events[0] >= window_seconds:
                    events.popleft()
                if len(events) >= limit:
                    retry_after = max(1, math.ceil(window_seconds - (now - events[0])))
                    raise HTTPException(
                        status_code=429,
                        detail="Too many requests. Please try again later.",
                        headers={"Retry-After": str(retry_after)},
                    )
                events.append(now)
                self._expires[key] = now + window_seconds

        return check


rate_limiter = InMemoryRateLimiter()
