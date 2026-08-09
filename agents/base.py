"""Shared utilities for ALNUA Hub agents."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

import httpx

from config.llm_runtime import (
    LLM_FALLBACK_STATUS,
    LLM_RETRY_BACKOFF_S,
    LLM_RETRYABLE_STATUS,
    http_timeout_s,
    max_attempts_per_model,
)
from config.settings import get_settings
from database.supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


def to_api_model_slug(model: str) -> str:
    """OpenRouter REST API expects provider/model without openrouter/ prefix."""
    m = model.strip()
    if m.startswith("openrouter/"):
        return m[len("openrouter/") :]
    return m


# Deprecated on OpenRouter — auto-upgrade at call time
_MODEL_ALIASES: dict[str, str] = {
    "x-ai/grok-3": "x-ai/grok-4.3",
}


def normalize_openrouter_model(model: str) -> str:
    """Resolve API slug + replace known-dead model IDs."""
    slug = to_api_model_slug(model)
    return _MODEL_ALIASES.get(slug, slug)


def openrouter_chat_completions_url(base_url: str) -> str:
    """Always return .../api/v1/chat/completions (never double-path)."""
    base = (base_url or "https://openrouter.ai/api/v1").strip().rstrip("/")
    if base.endswith("/chat/completions"):
        return base
    return f"{base}/chat/completions"


def to_crewai_model_slug(model: str) -> str:
    """CrewAI LLM wrapper expects openrouter/provider/model."""
    m = model.strip()
    if not m.startswith("openrouter/"):
        return f"openrouter/{m}"
    return m


def resolve_openrouter_model(agent_id: str) -> str:
    """Resolved model slug for OpenRouter REST API calls."""
    from config.agent_models import get_model_for_agent

    return normalize_openrouter_model(get_model_for_agent(agent_id))


def build_crewai_llm(agent_id: str, temperature: float = 0.3):
    """CrewAI LLM instance using per-agent model config + prompt-cache params."""
    from crewai import LLM

    from services.openrouter_prompt_cache import crewai_additional_params

    settings = get_settings()
    model = to_crewai_model_slug(resolve_openrouter_model(agent_id))
    extra = crewai_additional_params(agent_id, settings=settings)
    return LLM(
        model=model,
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        temperature=temperature,
        timeout=http_timeout_s(settings),
        additional_params=extra or None,
    )


class LLMClient:
    """OpenRouter chat completion client."""

    def __init__(self) -> None:
        self._settings = get_settings()

    def complete(
        self,
        system: str,
        user: str,
        model: str | None = None,
        agent_id: str | None = None,
        method_name: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> str:
        return self.chat(
            system=system,
            messages=[{"role": "user", "content": user}],
            model=model,
            agent_id=agent_id,
            method_name=method_name,
            temperature=temperature,
            max_tokens=max_tokens,
        )

    def chat(
        self,
        system: str,
        messages: list[dict[str, str]],
        model: str | None = None,
        agent_id: str | None = None,
        method_name: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        *,
        use_cache: bool = True,
    ) -> str:
        resolved_model, _enriched, payload_or_cache, headers, url = self._build_request(
            system=system,
            messages=messages,
            model=model,
            agent_id=agent_id,
            method_name=method_name,
            temperature=temperature,
            max_tokens=max_tokens,
            use_cache=use_cache,
        )
        if isinstance(payload_or_cache, str):
            return payload_or_cache

        actual_model, data = self._send_with_retry(url, headers, payload_or_cache, resolved_model)
        content = data["choices"][0]["message"]["content"]
        self._record_usage(
            data=data,
            agent_id=agent_id,
            model=actual_model,
            method_name=method_name,
        )
        self._store_cache(system, messages, actual_model, content, temperature, use_cache)
        return content

    async def complete_async(
        self,
        system: str,
        user: str,
        model: str | None = None,
        agent_id: str | None = None,
        method_name: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        *,
        use_cache: bool = True,
    ) -> str:
        """Native async LLM call — preferred in FastAPI async endpoints."""
        return await self.chat_async(
            system=system,
            messages=[{"role": "user", "content": user}],
            model=model,
            agent_id=agent_id,
            method_name=method_name,
            temperature=temperature,
            max_tokens=max_tokens,
            use_cache=use_cache,
        )

    async def chat_async(
        self,
        system: str,
        messages: list[dict[str, str]],
        model: str | None = None,
        agent_id: str | None = None,
        method_name: str = "",
        temperature: float = 0.7,
        max_tokens: int = 4096,
        *,
        use_cache: bool = True,
    ) -> str:
        """Native async OpenRouter call via httpx.AsyncClient."""
        resolved_model, _enriched, payload, headers, url = self._build_request(
            system=system,
            messages=messages,
            model=model,
            agent_id=agent_id,
            method_name=method_name,
            temperature=temperature,
            max_tokens=max_tokens,
            use_cache=use_cache,
        )
        if isinstance(payload, str):
            return payload

        actual_model, data = await self._send_with_retry_async(url, headers, payload, resolved_model)
        content = data["choices"][0]["message"]["content"]
        self._record_usage(
            data=data,
            agent_id=agent_id,
            model=actual_model,
            method_name=method_name,
        )
        self._store_cache(system, messages, actual_model, content, temperature, use_cache)
        return content

    def _fallback_models(self, resolved_model: str) -> list[str]:
        """Primary model, then one distinct fallback if the primary is overloaded/gone."""
        models = [resolved_model]
        fallback = normalize_openrouter_model(
            to_api_model_slug(self._settings.default_llm_model)
        )
        if fallback and fallback != resolved_model:
            models.append(fallback)
        return models

    def _send_with_retry(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        resolved_model: str,
    ) -> tuple[str, dict[str, Any]]:
        """POST with capped retries. Timeouts do not failover (avoids double burn).
        Client/auth 4xx (except 408/429) fail fast. Fallback only on 404/502/503."""
        last_exc: Exception | None = None
        attempts = max_attempts_per_model(self._settings)
        timeout = http_timeout_s(self._settings)
        for model_idx, model in enumerate(self._fallback_models(resolved_model)):
            model_payload = {**payload, "model": model}
            for attempt in range(attempts):
                try:
                    with httpx.Client(timeout=timeout) as client:
                        response = client.post(url, headers=headers, json=model_payload)
                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    last_exc = exc
                    if attempt < attempts - 1:
                        time.sleep(LLM_RETRY_BACKOFF_S * (2**attempt))
                        continue
                    raise last_exc from None
                if response.status_code >= 400:
                    if (
                        response.status_code in LLM_RETRYABLE_STATUS
                        and attempt < attempts - 1
                    ):
                        time.sleep(LLM_RETRY_BACKOFF_S * (2**attempt))
                        continue
                    last_exc = RuntimeError(
                        f"OpenRouter {response.status_code} model={model}: {response.text[:500]}"
                    )
                    if response.status_code not in LLM_RETRYABLE_STATUS:
                        if response.status_code in LLM_FALLBACK_STATUS and model_idx == 0:
                            break
                        raise last_exc from None
                    if response.status_code not in LLM_FALLBACK_STATUS:
                        raise last_exc from None
                    break
                return model, response.json()
            logger.warning("LLMClient: model %s failed, trying fallback if any", model)
        raise last_exc or RuntimeError("OpenRouter request failed with no response")

    async def _send_with_retry_async(
        self,
        url: str,
        headers: dict[str, str],
        payload: dict[str, Any],
        resolved_model: str,
    ) -> tuple[str, dict[str, Any]]:
        """Async twin of _send_with_retry — same retry/fallback semantics."""
        last_exc: Exception | None = None
        attempts = max_attempts_per_model(self._settings)
        timeout = http_timeout_s(self._settings)
        for model_idx, model in enumerate(self._fallback_models(resolved_model)):
            model_payload = {**payload, "model": model}
            for attempt in range(attempts):
                try:
                    async with httpx.AsyncClient(timeout=timeout) as client:
                        response = await client.post(url, headers=headers, json=model_payload)
                except (httpx.TimeoutException, httpx.NetworkError) as exc:
                    last_exc = exc
                    if attempt < attempts - 1:
                        await asyncio.sleep(LLM_RETRY_BACKOFF_S * (2**attempt))
                        continue
                    raise last_exc from None
                if response.status_code >= 400:
                    if (
                        response.status_code in LLM_RETRYABLE_STATUS
                        and attempt < attempts - 1
                    ):
                        await asyncio.sleep(LLM_RETRY_BACKOFF_S * (2**attempt))
                        continue
                    last_exc = RuntimeError(
                        f"OpenRouter {response.status_code} model={model}: {response.text[:500]}"
                    )
                    if response.status_code not in LLM_RETRYABLE_STATUS:
                        if response.status_code in LLM_FALLBACK_STATUS and model_idx == 0:
                            break
                        raise last_exc from None
                    if response.status_code not in LLM_FALLBACK_STATUS:
                        raise last_exc from None
                    break
                return model, response.json()
            logger.warning("LLMClient: model %s failed, trying fallback if any", model)
        raise last_exc or RuntimeError("OpenRouter request failed with no response")

    def _build_request(
        self,
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
            fallback = self._settings.agent_model or self._settings.default_llm_model
            resolved_model = resolved_model or to_api_model_slug(fallback)

        resolved_model = normalize_openrouter_model(resolved_model)

        if use_cache:
            try:
                if self._settings.llm_cache_enabled:
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

        ttl = prompt_cache_ttl(self._settings)
        cache_on = prompt_cache_enabled(self._settings)
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
            settings=self._settings,
        )
        headers = {
            "Authorization": f"Bearer {self._settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://alnua-hub.local",
            "X-Title": "ALNUA Hub",
        }
        if agent_id:
            headers["X-Session-Id"] = str(payload.get("session_id", f"alnua:{agent_id}"))
        url = openrouter_chat_completions_url(self._settings.openrouter_base_url)
        return resolved_model, static_system, payload, headers, url

    def _store_cache(
        self,
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
            if self._settings.llm_cache_enabled:
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

    def _record_usage(
        self,
        *,
        data: dict[str, Any],
        agent_id: str | None,
        model: str,
        method_name: str,
    ) -> None:
        """Track LLM usage in cost_monitor (+ optional Supabase legacy)."""
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
            cost_usd = record_call(
                agent_id=agent_id or "unknown",
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                method=method_name,
                cached_tokens=cache_stats["cached_tokens"],
                native_cost_usd=float(native_cost) if native_cost is not None else None,
            )
            try:
                from skills.skill_model_usage import log_usage

                log_usage(
                    agent_name=agent_id or "unknown",
                    model=model,
                    tokens_in=prompt_tokens,
                    tokens_out=completion_tokens,
                    cost_usd=cost_usd,
                    task_id=method_name or None,
                )
            except Exception:
                pass

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


def run_with_learning(
    agent_id: str,
    task: str,
    fn,
    *args,
    **kwargs,
) -> Any:
    """
    Wrapper universel : exécute fn(*args, **kwargs) puis déclenche
    l'apprentissage en arrière-plan selon le résultat.

    Usage dans n'importe quel agent :
        result = run_with_learning("marketing_agent", "Rédiger post", self.write_post, topic)

    Tous les agents héritent de cette fonction — aucun code dupliqué.
    """
    import traceback
    from skills.skill_agent_learning import is_task_failure

    try:
        result = fn(*args, **kwargs)
        outcome = str(result)[:600] if result else "Tâche complétée sans output"
        try:
            from skills.skill_agent_learning import learn_from_outcome
            learn_from_outcome(
                agent_id=agent_id,
                task=task,
                outcome=outcome,
                success=not is_task_failure(outcome),
            )
        except Exception:
            pass
        try:
            from services.competition import add_points
            add_points(agent_id, "task_completed", note=f"{task[:80]}")
        except Exception:
            pass
        try:
            from services.event_bus import emit

            emit(
                "task_completed",
                {"task": task[:200], "agent_id": agent_id},
                source_agent=agent_id,
            )
        except Exception:
            pass
        return result
    except Exception as exc:
        error_str = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()[-500:]}"
        try:
            from skills.skill_agent_learning import learn_from_failure
            learn_from_failure(agent_id=agent_id, task=task, error=error_str)
        except Exception:
            pass
        try:
            from services.event_bus import emit

            emit(
                "task_failed",
                {
                    "task": task[:200],
                    "agent_id": agent_id,
                    "error": error_str[:300],
                },
                source_agent=agent_id,
            )
        except Exception:
            pass
        raise


async def run_with_learning_async(
    agent_id: str,
    task: str,
    fn,
    *args,
    **kwargs,
) -> Any:
    """Async variant — runs sync fn in thread pool, preserves learning hooks."""
    return await asyncio.to_thread(run_with_learning, agent_id, task, fn, *args, **kwargs)


def log_agent_action(
    db: SupabaseClient,
    agent_name: str,
    action: str,
    input_summary: str,
    output_summary: str,
    status: str = "success",
    project_id: str | None = None,
) -> dict[str, Any]:
    return db.insert(
        "agent_logs",
        {
            "agent_name": agent_name,
            "action": action,
            "project_id": project_id,
            "input_summary": input_summary[:2000],
            "output_summary": output_summary[:2000],
            "status": status,
        },
    )


def parse_json_response(text: str) -> dict[str, Any]:
    """Extract JSON object from LLM response (handles markdown fences)."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        lines = lines[1:] if lines[0].startswith("```") else lines
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    return json.loads(cleaned)
