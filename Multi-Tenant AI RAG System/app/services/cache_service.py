"""
Synchronous Redis caching service with tenant-scoped key namespacing.
Gracefully degrades when Redis is unavailable.
"""

import json
import logging
from typing import Any, Callable

import redis

from app.config import settings

logger = logging.getLogger(__name__)

# Module-level Redis client (lazy init)
_redis_client: redis.Redis | None = None


def _get_redis() -> redis.Redis | None:
    """Get Redis client. Returns None if Redis is unavailable."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    try:
        _redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        _redis_client.ping()
        return _redis_client
    except Exception:
        logger.warning("Redis unavailable — caching disabled")
        return None


class CacheService:
    """Synchronous Redis cache with tenant-scoped key namespacing."""

    DEFAULT_TTL = 300  # 5 minutes

    def __init__(self):
        self.redis = _get_redis()

    @property
    def available(self) -> bool:
        return self.redis is not None

    def _key(self, namespace: str, tenant_id: str, key: str) -> str:
        return f"cache:{namespace}:{tenant_id}:{key}"

    def get(self, namespace: str, tenant_id: str, key: str) -> Any | None:
        if not self.available:
            return None
        try:
            from app.utils.metrics import CACHE_HITS, CACHE_MISSES

            raw = self.redis.get(self._key(namespace, tenant_id, key))
            if raw is not None:
                CACHE_HITS.inc()
                return json.loads(raw)
            CACHE_MISSES.inc()
        except Exception:
            logger.debug("Cache get failed", exc_info=True)
        return None

    def set(
        self,
        namespace: str,
        tenant_id: str,
        key: str,
        value: Any,
        ttl: int | None = None,
    ) -> None:
        if not self.available:
            return
        try:
            self.redis.setex(
                self._key(namespace, tenant_id, key),
                ttl or self.DEFAULT_TTL,
                json.dumps(value, default=str),
            )
        except Exception:
            logger.debug("Cache set failed", exc_info=True)

    def get_or_set(
        self,
        namespace: str,
        tenant_id: str,
        key: str,
        factory: Callable[[], Any],
        ttl: int | None = None,
    ) -> Any:
        cached = self.get(namespace, tenant_id, key)
        if cached is not None:
            return cached
        value = factory()
        self.set(namespace, tenant_id, key, value, ttl)
        return value

    def invalidate(
        self, namespace: str, tenant_id: str, key: str | None = None
    ) -> int:
        """Invalidate specific key or all keys in namespace for tenant."""
        if not self.available:
            return 0
        try:
            if key:
                return self.redis.delete(self._key(namespace, tenant_id, key))
            # Pattern-based deletion for all tenant keys in namespace
            pattern = f"cache:{namespace}:{tenant_id}:*"
            keys = list(self.redis.scan_iter(match=pattern, count=100))
            if keys:
                return self.redis.delete(*keys)
        except Exception:
            logger.debug("Cache invalidate failed", exc_info=True)
        return 0

    def invalidate_tenant(self, tenant_id: str) -> int:
        """Invalidate ALL cached data for a tenant."""
        if not self.available:
            return 0
        try:
            pattern = f"cache:*:{tenant_id}:*"
            keys = list(self.redis.scan_iter(match=pattern, count=500))
            if keys:
                return self.redis.delete(*keys)
        except Exception:
            logger.debug("Cache invalidate_tenant failed", exc_info=True)
        return 0
