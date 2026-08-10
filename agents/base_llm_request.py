"""OpenRouter LLM request building, caching, and usage tracking."""

from __future__ import annotations

from typing import Any

from agents.base_models import (
    normalize_openrouter_model,
    openrouter_chat_completions_url,
    resolve_openrouter_model,
    to_api_model_slug,
)
from config.settings import Settings


def build_request(
    settings: Settings,
    *,
    system: str,
    messages: list[dict[str, str]],
    model: str | None,
    agent_id: str | None,
    method_name: str,
    temperature: float,
    max_tokens: int,
    use_cache: bool,
) -> tuple[str, str, dict[str, Any] | str, dict[str, str], str]:
    """Shared request builder; returns cache hit as str in payload position."""
    resolved_model = to_api_model_slug(model) if model else None
    if not resolved_model and agent_id and method_name:
        try:
            from services.llm_router import route_to_model

            user_text = " ".join(
                m.get("content", "") for m in messages if m.get("role") == "user"
            )
            resolved_model = to_api_model_slug(
                route_to_model(agent_id, user_text, method_name)
            )
        except Exception:
            pass
    if not resolved_model:
        if agent_id:
            try:
                resolved_model = resolve_openrouter_model(agent_id)
            except Exception:
                pass
        fallback = settings.agent_model or settings.default_llm_model
        resolved_model = resolved_model or to_api_model_slug(fallback)

    resolved_model = normalize_openrouter_model(resolved_model)

    if use_cache:
        try:
            if settings.llm_cache_enabled:
                from services.llm_cache import llm_cache
                cached = llm_cache.get(
                    system=system,
                    messages=messages,
                    model=resolved_model,
                    temperature=temperature,
                )
                if cached is not None:
                    return resolved_model, system, cached, {}, ""
        except Exception:
            pass

    static_system = system
    dynamic_tail = ""
    if agent_id:
        try:
            from config.agent_personas import get_competitive_context, get_persona
            persona = get_persona(agent_id)
            if persona and persona.get("competitive", False):
                from services.competition import get_scores
                competitive_block = get_competitive_context(agent_id, get_scores())
                if competitive_block:
                    dynamic_tail = competitive_block
        except Exception:
            pass

    from services.openrouter_prompt_cache import (
        apply_prompt_cache_to_payload,
        build_system_message,
        prompt_cache_enabled,
        prompt_cache_ttl,
    )

    ttl = prompt_cache_ttl(settings)
    cache_on = prompt_cache_enabled(settings)
    or_messages: list[dict[str, Any]] = [
        build_system_message(
            static_system,
            model=resolved_model,
            ttl=ttl,
            enable=cache_on,
        )
    ]
    if dynamic_tail:
        or_messages.append({"role": "system", "content": dynamic_tail})
    or_messages.extend(messages)

    payload: dict[str, Any] = {
        "model": resolved_model,
        "messages": or_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    payload = apply_prompt_cache_to_payload(
        payload,
        model=resolved_model,
        agent_id=agent_id,
        settings=settings,
    )
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://alnua-hub.local",
        "X-Title": "ALNUA Hub",
    }
    if agent_id:
        headers["X-Session-Id"] = str(payload.get("session_id", f"alnua:{agent_id}"))
    url = openrouter_chat_completions_url(settings.openrouter_base_url)
    return resolved_model, static_system, payload, headers, url


def store_cache(
    settings: Settings,
    *,
    system: str,
    messages: list[dict[str, str]],
    model: str,
    content: str,
    temperature: float,
    use_cache: bool,
) -> None:
    if not use_cache:
        return
    try:
        if settings.llm_cache_enabled:
            from services.llm_cache import llm_cache
            llm_cache.set(
                system=system,
                messages=messages,
                model=model,
                response=content,
                temperature=temperature,
            )
    except Exception:
        pass


def record_usage(
    *,
    data: dict[str, Any],
    agent_id: str | None,
    model: str,
    method_name: str,
) -> None:
    """Track LLM usage in cost_monitor (single source of truth)."""
    try:
        usage = data.get("usage") or {}
        prompt_tokens = int(usage.get("prompt_tokens") or 0)
        completion_tokens = int(usage.get("completion_tokens") or 0)
        if not prompt_tokens and not completion_tokens:
            return

        from services.cost_monitor import check_budget_alert, record_call
        from services.openrouter_prompt_cache import extract_cache_stats

        cache_stats = extract_cache_stats(usage)
        native_cost = usage.get("cost")
        record_call(
            agent_id=agent_id or "unknown",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            method=method_name,
            cached_tokens=cache_stats["cached_tokens"],
            native_cost_usd=float(native_cost) if native_cost is not None else None,
        )

        alert = check_budget_alert()
        if alert.get("alert"):
            from services.event_bus import emit

            emit(
                "budget_alert",
                {
                    "severity": alert.get("severity"),
                    "spent_usd": alert.get("spent_usd"),
                    "daily_budget_usd": alert.get("daily_budget_usd"),
                },
                source_agent=agent_id or "system",
            )
    except Exception:
        pass
