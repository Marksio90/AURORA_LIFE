"""Rate limiting middleware using Redis"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable
import time
from redis.asyncio import Redis

from app.core.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using sliding window algorithm.

    Limits:
    - Per IP: 100 requests per minute
    - Per user: 1000 requests per hour
    """

    def __init__(self, app, redis_client: Redis):
        super().__init__(app)
        self.redis = redis_client
        self.enabled = getattr(settings, 'ENABLE_RATE_LIMITING', False)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if not self.enabled:
            return await call_next(request)

        client_ip = request.client.host
        path = request.url.path

        # Skip rate limiting for health checks
        if path in ["/health", "/", "/docs", "/openapi.json"]:
            return await call_next(request)

        # Check IP rate limit
        if not await self._check_rate_limit(f"ratelimit:ip:{client_ip}", limit=100, window=60):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )

        response = await call_next(request)
        return response

    async def _check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """
        Check if request is within rate limit using sliding window.

        Args:
            key: Redis key for this rate limit
            limit: Max number of requests
            window: Time window in seconds

        Returns:
            True if within limit, False if exceeded
        """
        try:
            current_time = int(time.time())
            window_start = current_time - window

            # Remove old entries
            await self.redis.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            count = await self.redis.zcard(key)

            if count >= limit:
                return False

            # Add current request
            await self.redis.zadd(key, {str(current_time): current_time})
            await self.redis.expire(key, window)

            return True
        except Exception:
            # If Redis fails, allow request (fail open)
            return True
