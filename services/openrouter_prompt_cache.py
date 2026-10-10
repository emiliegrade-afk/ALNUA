"""OpenRouter prompt caching helpers — stable prefixes + sticky sessions.

OpenRouter docs (prompt-caching):
- DeepSeek / Z.AI / Moonshot: automatic cache (stable prefix + session_id)
- Anthropic / Gemini explicit: cache_control on content blocks
- Top-level cache_control enables automatic Anthropic-style caching
- session_id pins provider sticky routing for multi-turn / tool loops

Goal: SYSTEM_PROMPT + tool schemas (static) paid once; dynamic tails stay uncached.
"""

from __future__ import annotations

from typing import Any

# Providers that benefit from explicit per-block cache_control
_EXPLICIT_CACHE_PREFIXES: tuple[str, ...] = (
    "anthropic/",
    "google/gemini",
    "qwen/",
    "deepseek/deepseek-v3.2",
)

# Default TTL for Anthropic-compatible breakpoints (longer agent sessions)
_DEFAULT_TTL = "1h"


def prompt_cache_enabled(settings: Any | None = None) -> bool:
    if settings is None:
        try:
            from config.settings import get_settings

            settings = get_settings()
        except Exception:
            return True
    return bool(getattr(settings, "openrouter_prompt_cache_enabled", True))


def prompt_cache_ttl(settings: Any | None = None) -> str:
    if settings is None:
        try:
            from config.settings import get_settings

            settings = get_settings()
        except Exception:
            return _DEFAULT_TTL
    ttl = str(getattr(settings, "openrouter_prompt_cache_ttl", _DEFAULT_TTL) or _DEFAULT_TTL)
    return ttl if ttl in ("5m", "1h") else _DEFAULT_TTL


def model_needs_explicit_cache_control(model: str) -> bool:
    m = (model or "").strip().lower()
    if m.startswith("openrouter/"):
        m = m[len("openrouter/") :]
    return any(m.startswith(p) for p in _EXPLICIT_CACHE_PREFIXES)


def session_id_for_agent(agent_id: str | None, method_name: str = "") -> str:
    """Sticky key per agent so SYSTEM + tools stay warm across methods."""
    aid = (agent_id or "hub").strip().lower() or "hub"
    # Cap 256 chars (OpenRouter limit)
    sid = f"alnua:{aid}"
    if method_name and len(sid) + len(method_name) + 1 < 200:
        # Optional method suffix only for very distinct long-running jobs
        pass
    return sid[:256]


def _cache_control(ttl: str) -> dict[str, str]:
    cc: dict[str, str] = {"type": "ephemeral"}
    if ttl == "1h":
        cc["ttl"] = "1h"
    return cc


def build_system_message(
    static_system: str,
    *,
    model: str,
    ttl: str = _DEFAULT_TTL,
    enable: bool = True,
) -> dict[str, Any]:
    """System message with optional explicit cache breakpoint on the static body."""
    text = static_system or ""
    if not enable or not model_needs_explicit_cache_control(model):
        return {"role": "system", "content": text}
    return {
        "role": "system",
        "content": [
            {
                "type": "text",
                "text": text,
                "cache_control": _cache_control(ttl),
            }
        ],
    }


def apply_prompt_cache_to_payload(
    payload: dict[str, Any],
    *,
    model: str,
    agent_id: str | None = None,
    settings: Any | None = None,
) -> dict[str, Any]:
    """Mutate/return payload with session_id + cache_control for OpenRouter."""
    if not prompt_cache_enabled(settings):
        return payload

    ttl = prompt_cache_ttl(settings)
    out = dict(payload)

    # Sticky routing — critical for DeepSeek / MiniMax / Z.AI automatic cache hits
    out["session_id"] = session_id_for_agent(agent_id)

    # Top-level automatic caching (Anthropic providers + harmless elsewhere)
    out["cache_control"] = _cache_control(ttl)

    # Rewrite system message to multipart + breakpoint when provider needs it
    messages = list(out.get("messages") or [])
    if messages and messages[0].get("role") == "system":
        first = messages[0]
        content = first.get("content")
        if isinstance(content, str):
            messages[0] = build_system_message(
                content, model=model, ttl=ttl, enable=True
            )
            out["messages"] = messages

    return out


def crewai_additional_params(
    agent_id: str,
    *,
    settings: Any | None = None,
) -> dict[str, Any]:
    """Params merged into CrewAI LLM calls (tool-heavy agents).

    CrewAI forwards ``additional_params`` as **kwargs to the OpenAI client, so
    OpenRouter-only body fields must be wrapped in ``extra_body`` — passing them
    top-level raises ``Completions.create() got an unexpected keyword argument``
    (bug trouvé 2026-09-08 : tout agent CrewAI cassait à l'appel).
    """
    if not prompt_cache_enabled(settings):
        return {}
    ttl = prompt_cache_ttl(settings)
    return {
        "extra_body": {
            "session_id": session_id_for_agent(agent_id),
            "cache_control": _cache_control(ttl),
        }
    }


def extract_cache_stats(usage: dict[str, Any] | None) -> dict[str, int]:
    """Pull cached_tokens / cache_write_tokens from OpenRouter usage."""
    usage = usage or {}
    details = usage.get("prompt_tokens_details") or usage.get("input_tokens_details") or {}
    return {
        "cached_tokens": int(details.get("cached_tokens") or 0),
        "cache_write_tokens": int(details.get("cache_write_tokens") or 0),
    }
