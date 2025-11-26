"""
Rate Limiting Middleware for expensive ML operations
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple
import time
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse of expensive ML endpoints.

    Uses sliding window algorithm for rate limiting.
    """

    def __init__(self, app, rate_limit: int = 10, window_seconds: int = 60):
        """
        Args:
            app: FastAPI application
            rate_limit: Maximum requests allowed in window
            window_seconds: Time window in seconds
        """
        super().__init__(app)
        self.rate_limit = rate_limit
        self.window_seconds = window_seconds

        # In-memory store: {(user_id, endpoint): deque of timestamps}
        # In production, use Redis for distributed rate limiting
        self.request_history: Dict[Tuple[str, str], deque] = defaultdict(deque)

        # Define expensive endpoints that need rate limiting
        self.rate_limited_endpoints = {
            "/api/ai/analyze/": 5,  # 5 requests per minute
            "/api/ai/predict/energy/": 10,  # 10 requests per minute
            "/api/ai/predict/mood/": 10,
            "/api/ai/recommend/": 10,
            "/api/ai/agents/run-all/": 3,  # Very expensive - only 3 per minute
            "/api/ai/whatif/simulate/": 5,  # Expensive simulations - 5 per minute
        }

    async def dispatch(self, request: Request, call_next):
        """Process request and apply rate limiting."""

        # Check if this endpoint needs rate limiting
        endpoint = request.url.path
        custom_limit = None

        for pattern, limit in self.rate_limited_endpoints.items():
            if endpoint.startswith(pattern):
                custom_limit = limit
                break

        # If not a rate-limited endpoint, proceed normally
        if custom_limit is None:
            return await call_next(request)

        # Extract user identifier (from JWT or IP address)
        user_id = self._get_user_identifier(request)
        key = (user_id, endpoint)

        # Check rate limit
        current_time = time.time()
        is_allowed, remaining = self._check_rate_limit(
            key, current_time, custom_limit
        )

        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for user {user_id} on endpoint {endpoint}"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {custom_limit} requests per minute.",
                    "retry_after": self.window_seconds
                },
                headers={"Retry-After": str(self.window_seconds)}
            )

        # Add rate limit headers to response
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(custom_limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(current_time + self.window_seconds))

        return response

    def _get_user_identifier(self, request: Request) -> str:
        """Extract user identifier from request (IP for now, JWT in production)"""
        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"

    def _check_rate_limit(
        self, key: Tuple[str, str], current_time: float, limit: int
    ) -> Tuple[bool, int]:
        """Check if request is within rate limit using sliding window."""
        history = self.request_history[key]

        # Remove timestamps outside the window
        cutoff_time = current_time - self.window_seconds
        while history and history[0] < cutoff_time:
            history.popleft()

        # Check if limit exceeded
        if len(history) >= limit:
            return False, 0

        # Add current request timestamp
        history.append(current_time)

        remaining = limit - len(history)
        return True, remaining
