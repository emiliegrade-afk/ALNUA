"""LLM runtime knobs — timeouts, retries, CrewAI iteration caps.

Keeps OpenRouter spend under control when tools/MCP fail or hang.
"""

from __future__ import annotations

from typing import Any

# HTTP to OpenRouter
LLM_HTTP_TIMEOUT_S = 60.0
LLM_HTTP_TIMEOUT_LONG_S = 120.0  # coding / long generations only
LLM_MAX_ATTEMPTS_PER_MODEL = 2
LLM_RETRY_BACKOFF_S = 1.5

# Retry same model on these; fallback model only when primary is gone/overloaded
LLM_RETRYABLE_STATUS = frozenset({408, 429, 500, 502, 503, 504})
LLM_FALLBACK_STATUS = frozenset({404, 502, 503})

# CrewAI agent loops — each iter re-sends full tool schemas (expensive without cache)
CREWAI_MAX_ITER_DEFAULT = 6
CREWAI_MAX_ITER_COO = 8
CREWAI_MAX_ITER_LIGHT = 5

# skill_retry_loop — tool/MCP auth failures must not burn 3 LLM cycles
RETRY_LOOP_MAX_ATTEMPTS = 3
RETRY_LOOP_TOOL_MAX_ATTEMPTS = 1
RETRY_LOOP_DELAYS_S = (0, 20, 40)


def http_timeout_s(settings: Any | None = None, *, long: bool = False) -> float:
    if settings is None:
        try:
            from config.settings import get_settings

            settings = get_settings()
        except Exception:
            settings = None
    if long:
        return float(
            getattr(settings, "llm_http_timeout_long_s", LLM_HTTP_TIMEOUT_LONG_S)
            if settings
            else LLM_HTTP_TIMEOUT_LONG_S
        )
    return float(
        getattr(settings, "llm_http_timeout_s", LLM_HTTP_TIMEOUT_S)
        if settings
        else LLM_HTTP_TIMEOUT_S
    )


def max_attempts_per_model(settings: Any | None = None) -> int:
    if settings is None:
        try:
            from config.settings import get_settings

            settings = get_settings()
        except Exception:
            return LLM_MAX_ATTEMPTS_PER_MODEL
    raw = getattr(settings, "llm_max_attempts_per_model", LLM_MAX_ATTEMPTS_PER_MODEL)
    return max(1, min(int(raw), 3))
