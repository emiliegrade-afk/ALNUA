"""Sliding-window rate limiter — Redis-backed with in-memory fallback."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class RateLimitConfig:
    max_requests: int = 20
    window_seconds: int = 60


@dataclass
class _Bucket:
    timestamps: list[float] = field(default_factory=list)


class RateLimiter:
    """Thread-safe sliding window — uses Redis sorted sets when available."""

    def __init__(self, *, prefix: str = "rl") -> None:
        self._buckets: dict[str, _Bucket] = defaultdict(_Bucket)
        self._lock = Lock()
        self._prefix = prefix

    def _redis_key(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    def _redis_allowed(self, key: str, cfg: RateLimitConfig) -> bool | None:
        """Return True/False if Redis handled it, None if unavailable."""
        try:
            from services.redis_client import get_redis

            r = get_redis()
            if r is None:
                return None
            import time as _time

            rk = self._redis_key(key)
            now = _time.time()
            pipe = r.pipeline()
            pipe.zremrangebyscore(rk, 0, now - cfg.window_seconds)
            pipe.zcard(rk)
            pipe.zadd(rk, {str(now): now})
            pipe.expire(rk, cfg.window_seconds + 1)
            results = pipe.execute()
            count = results[1]
            if count >= cfg.max_requests:
                r.zrem(rk, str(now))
                return False
            return True
        except Exception:
            return None

    def is_allowed(self, key: str, config: RateLimitConfig | None = None) -> bool:
        cfg = config or RateLimitConfig()
        redis_result = self._redis_allowed(key, cfg)
        if redis_result is not None:
            return redis_result

        now = time.monotonic()
        cutoff = now - cfg.window_seconds
        with self._lock:
            bucket = self._buckets[key]
            bucket.timestamps = [t for t in bucket.timestamps if t > cutoff]
            if len(bucket.timestamps) >= cfg.max_requests:
                return False
            bucket.timestamps.append(now)
            return True

    def remaining(self, key: str, config: RateLimitConfig | None = None) -> int:
        cfg = config or RateLimitConfig()
        try:
            from services.redis_client import get_redis
            import time as _time

            r = get_redis()
            if r is not None:
                rk = self._redis_key(key)
                now = _time.time()
                r.zremrangebyscore(rk, 0, now - cfg.window_seconds)
                count = r.zcard(rk)
                return max(0, cfg.max_requests - count)
        except Exception:
            pass

        now = time.monotonic()
        cutoff = now - cfg.window_seconds
        with self._lock:
            bucket = self._buckets[key]
            active = [t for t in bucket.timestamps if t > cutoff]
            return max(0, cfg.max_requests - len(active))

    def reset(self, key: str) -> None:
        try:
            from services.redis_client import get_redis

            r = get_redis()
            if r is not None:
                r.delete(self._redis_key(key))
        except Exception:
            pass
        with self._lock:
            self._buckets.pop(key, None)


api_limiter = RateLimiter(prefix="rl:api")
telegram_limiter = RateLimiter(prefix="rl:tg")
assistant_limiter = RateLimiter(prefix="rl:assistant")

TELEGRAM_LIMIT = RateLimitConfig(max_requests=10, window_seconds=60)
ASSISTANT_LIMIT = RateLimitConfig(max_requests=30, window_seconds=60)
API_LIMIT = RateLimitConfig(max_requests=120, window_seconds=60)
