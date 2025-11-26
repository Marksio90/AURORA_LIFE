"""
Redis caching layer for API responses
"""
from typing import Optional, Any, Callable
from functools import wraps
import json
import hashlib
from redis.asyncio import Redis

from app.core.config import settings


class CacheManager:
    """
    Redis-based cache manager.

    Features:
    - JSON serialization
    - Configurable TTL
    - Cache invalidation
    - Key namespacing
    """

    def __init__(self, redis: Redis, namespace: str = "cache"):
        self.redis = redis
        self.namespace = namespace
        self.default_ttl = 300  # 5 minutes

    def _make_key(self, key: str) -> str:
        """Create namespaced cache key."""
        return f"{self.namespace}:{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        full_key = self._make_key(key)
        value = await self.redis.get(full_key)

        if value is None:
            return None

        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return value

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set value in cache with TTL."""
        full_key = self._make_key(key)

        # Serialize to JSON if not string
        if not isinstance(value, str):
            value = json.dumps(value)

        ttl = ttl or self.default_ttl
        return await self.redis.setex(full_key, ttl, value)

    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        full_key = self._make_key(key)
        return await self.redis.delete(full_key) > 0

    async def clear_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        full_pattern = self._make_key(pattern)
        keys = []

        async for key in self.redis.scan_iter(match=full_pattern):
            keys.append(key)

        if keys:
            return await self.redis.delete(*keys)
        return 0

    def cache_key(self, *args, **kwargs) -> str:
        """Generate cache key from function arguments."""
        # Create deterministic key from arguments
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_str = ":".join(key_parts)

        # Hash for consistent length
        return hashlib.md5(key_str.encode()).hexdigest()


def cached(
    ttl: int = 300,
    key_prefix: str = "",
    skip_if: Optional[Callable] = None
):
    """
    Decorator for caching function results.

    Usage:
        @cached(ttl=600, key_prefix="user")
        async def get_user(user_id: int):
            ...

    Args:
        ttl: Cache TTL in seconds
        key_prefix: Prefix for cache key
        skip_if: Optional function to determine if caching should be skipped
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Check if should skip caching
            if skip_if and skip_if(*args, **kwargs):
                return await func(*args, **kwargs)

            # Get cache manager from kwargs or create new one
            cache: Optional[CacheManager] = kwargs.get('cache')
            if not cache:
                return await func(*args, **kwargs)

            # Generate cache key
            cache_key = f"{key_prefix}:{cache.cache_key(*args, **kwargs)}"

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator
