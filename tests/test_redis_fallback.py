"""Tests for Redis/RQ graceful fallback when Redis unavailable."""

from __future__ import annotations

from unittest.mock import patch

from services.llm_cache import LLMCache
from services.rate_limiter import RateLimitConfig, RateLimiter


def test_rate_limiter_memory_fallback() -> None:
    with patch("services.redis_client.get_redis", return_value=None):
        limiter = RateLimiter(prefix="test")
        cfg = RateLimitConfig(max_requests=2, window_seconds=60)
        assert limiter.is_allowed("k1", cfg) is True
        assert limiter.is_allowed("k1", cfg) is True
        assert limiter.is_allowed("k1", cfg) is False


def test_llm_cache_works_without_redis() -> None:
    cache = LLMCache()
    msgs = [{"role": "user", "content": "hello"}]
    with patch("services.redis_client.get_redis", return_value=None):
        cache.set(system="s", messages=msgs, model="m", response="world", temperature=0.0)
    assert cache.get(system="s", messages=msgs, model="m", temperature=0.0) == "world"
