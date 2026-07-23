"""LLM response cache — in-memory + optional Redis TTL backend."""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry:
    response: str
    created_at: float
    model: str
    hits: int = 0


class LLMCache:
    """Thread-safe cache with in-memory + Redis layers."""

    def __init__(self, *, default_ttl_s: int = 3600, max_entries: int = 500) -> None:
        self._store: dict[str, CacheEntry] = {}
        self._lock = Lock()
        self._default_ttl_s = default_ttl_s
        self._max_entries = max_entries

    def _make_key(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
    ) -> str:
        payload = json.dumps(
            {"system": system, "messages": messages, "model": model, "temp": temperature},
            sort_keys=True,
            ensure_ascii=False,
        )
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        model: str,
        temperature: float = 0.0,
        ttl_s: int | None = None,
    ) -> str | None:
        if temperature > 0.1:
            return None

        key = self._make_key(system=system, messages=messages, model=model, temperature=temperature)
        ttl = ttl_s or self._default_ttl_s

        try:
            from services.redis_client import redis_get
            cached = redis_get(f"llm:{key}")
            if cached is not None:
                return cached
        except Exception:
            pass

        now = time.monotonic()
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            if now - entry.created_at > ttl:
                del self._store[key]
                return None
            entry.hits += 1
            return entry.response

    def set(
        self,
        *,
        system: str,
        messages: list[dict[str, str]],
        model: str,
        response: str,
        temperature: float = 0.0,
    ) -> None:
        if temperature > 0.1:
            return

        key = self._make_key(system=system, messages=messages, model=model, temperature=temperature)

        try:
            from config.settings import get_settings
            from services.redis_client import redis_set
            redis_set(f"llm:{key}", response, ttl_s=get_settings().llm_cache_ttl_s)
        except Exception:
            pass

        with self._lock:
            if len(self._store) >= self._max_entries:
                oldest_key = min(self._store, key=lambda k: self._store[k].created_at)
                del self._store[oldest_key]
            self._store[key] = CacheEntry(
                response=response,
                created_at=time.monotonic(),
                model=model,
            )

    def invalidate(self, pattern: str) -> int:
        removed = 0
        with self._lock:
            to_delete = [k for k, v in self._store.items() if pattern in v.response]
            for k in to_delete:
                del self._store[k]
                removed += 1
        return removed

    def stats(self) -> dict[str, Any]:
        with self._lock:
            total_hits = sum(e.hits for e in self._store.values())
            return {
                "entries": len(self._store),
                "total_hits": total_hits,
                "max_entries": self._max_entries,
                "default_ttl_s": self._default_ttl_s,
            }


llm_cache = LLMCache()
