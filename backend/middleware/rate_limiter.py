"""Simple in-memory rate limiter — sliding window per IP.

Uses a dict of deques; adequate for a single-process API server.
For multi-process deployments, swap the backend for Redis.
"""
import time
import logging
from collections import defaultdict, deque
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger("fingraph.ratelimit")

# Default limits — override via constructor
DEFAULT_WINDOW_SECONDS = 60
DEFAULT_MAX_REQUESTS = 120  # per window per IP


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, window: int = DEFAULT_WINDOW_SECONDS, max_requests: int = DEFAULT_MAX_REQUESTS):
        super().__init__(app)
        self._window = window
        self._max = max_requests
        self._buckets: dict[str, deque] = defaultdict(deque)

    def _is_allowed(self, ip: str) -> bool:
        now = time.monotonic()
        bucket = self._buckets[ip]
        cutoff = now - self._window

        # Evict expired timestamps
        while bucket and bucket[0] < cutoff:
            bucket.popleft()

        if len(bucket) >= self._max:
            return False

        bucket.append(now)
        return True

    async def dispatch(self, request: Request, call_next):
        # Skip rate-limiting for health checks
        if request.url.path in ("/health", "/"):
            return await call_next(request)

        ip = request.client.host if request.client else "unknown"
        if not self._is_allowed(ip):
            logger.warning("Rate limit hit ip=%s path=%s", ip, request.url.path)
            return JSONResponse(
                status_code=429,
                content={"success": False, "error": "Too many requests. Please slow down."},
                headers={"Retry-After": str(self._window)},
            )

        return await call_next(request)
