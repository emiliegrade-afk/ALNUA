"""Redis client — optional backend for cache, rate limits, and RQ queue."""

from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

_redis_client: Any = None
_redis_available: bool | None = None


def get_redis() -> Any | None:
    """Return Redis client if REDIS_URL is configured, else None."""
    global _redis_client, _redis_available
    if _redis_available is False:
        return None
    if _redis_client is not None:
        return _redis_client
    try:
        from config.settings import get_settings
        url = get_settings().redis_url.strip()
        if not url:
            _redis_available = False
            return None
        import redis
        _redis_client = redis.from_url(url, decode_responses=True)
        _redis_client.ping()
        _redis_available = True
        logger.info("Redis connected: %s", url.split("@")[-1])
        return _redis_client
    except Exception as exc:
        logger.warning("Redis unavailable — falling back to in-memory: %s", exc)
        _redis_available = False
        return None


def redis_get(key: str) -> str | None:
    r = get_redis()
    if not r:
        return None
    try:
        return r.get(key)
    except Exception:
        return None


def redis_set(key: str, value: str, *, ttl_s: int = 3600) -> None:
    r = get_redis()
    if not r:
        return
    try:
        r.setex(key, ttl_s, value)
    except Exception:
        pass


def redis_get_json(key: str) -> Any | None:
    raw = redis_get(key)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def redis_set_json(key: str, value: Any, *, ttl_s: int = 3600) -> None:
    redis_set(key, json.dumps(value, ensure_ascii=False), ttl_s=ttl_s)
