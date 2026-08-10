"""OpenRouter LLM transport — retry and model fallback."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

from agents.base_models import normalize_openrouter_model, to_api_model_slug
from config.llm_runtime import (
    LLM_FALLBACK_STATUS,
    LLM_RETRY_BACKOFF_S,
    LLM_RETRYABLE_STATUS,
    http_timeout_s,
    max_attempts_per_model,
)
from config.settings import Settings

logger = logging.getLogger(__name__)


def fallback_models(settings: Settings, resolved_model: str) -> list[str]:
    """Primary model, then one distinct fallback if the primary is overloaded/gone."""
    models = [resolved_model]
    fallback = normalize_openrouter_model(
        to_api_model_slug(settings.default_llm_model)
    )
    if fallback and fallback != resolved_model:
        models.append(fallback)
    return models


def send_with_retry(
    settings: Settings,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    resolved_model: str,
) -> tuple[str, dict[str, Any]]:
    """POST with capped retries. Timeouts do not failover (avoids double burn)."""
    last_exc: Exception | None = None
    attempts = max_attempts_per_model(settings)
    timeout = http_timeout_s(settings)
    for model_idx, model in enumerate(fallback_models(settings, resolved_model)):
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


async def send_with_retry_async(
    settings: Settings,
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    resolved_model: str,
) -> tuple[str, dict[str, Any]]:
    """Async twin of send_with_retry — same retry/fallback semantics."""
    last_exc: Exception | None = None
    attempts = max_attempts_per_model(settings)
    timeout = http_timeout_s(settings)
    for model_idx, model in enumerate(fallback_models(settings, resolved_model)):
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
