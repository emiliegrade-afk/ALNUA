"""OpenRouter chat completion client with local-LLM failover on credit exhaustion."""

from __future__ import annotations

import logging

from agents.base_llm_request import build_request, record_usage, store_cache
from agents.base_llm_transport import (
    OpenRouterCreditExhausted,
    send_with_retry,
    send_with_retry_async,
)
from config.settings import get_settings

logger = logging.getLogger(__name__)


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
        resolved_model, _enriched, payload_or_cache, headers, url = build_request(
            self._settings,
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

        try:
            actual_model, data = send_with_retry(
                self._settings, url, headers, payload_or_cache, resolved_model,
            )
        except OpenRouterCreditExhausted as exc:
            local = self._local_fallback(payload_or_cache, exc)
            if local is not None:
                return local
            raise
        content = data["choices"][0]["message"]["content"]
        record_usage(
            data=data,
            agent_id=agent_id,
            model=actual_model,
            method_name=method_name,
        )
        store_cache(
            self._settings,
            system=system,
            messages=messages,
            model=actual_model,
            content=content,
            temperature=temperature,
            use_cache=use_cache,
        )
        return content

    def _local_fallback(self, payload: dict, exc: Exception) -> str | None:
        """Bascule vers le modèle local si OpenRouter n'a plus de crédit (402)."""
        from services import local_llm

        if not local_llm.local_llm_available():
            return None
        if not local_llm.fallback_on_credit_enabled():
            return None
        logger.warning("OpenRouter à court de crédits — bascule locale (%s)", exc)
        try:
            return local_llm.complete_local_sync(payload)
        except Exception as local_exc:
            logger.error("Bascule locale échouée : %s", local_exc)
            return None

    async def _local_fallback_async(self, payload: dict, exc: Exception) -> str | None:
        from services import local_llm

        if not local_llm.local_llm_available():
            return None
        if not local_llm.fallback_on_credit_enabled():
            return None
        logger.warning("OpenRouter à court de crédits — bascule locale (%s)", exc)
        try:
            return await local_llm.complete_local_async(payload)
        except Exception as local_exc:
            logger.error("Bascule locale échouée : %s", local_exc)
            return None

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
        resolved_model, _enriched, payload, headers, url = build_request(
            self._settings,
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

        try:
            actual_model, data = await send_with_retry_async(
                self._settings, url, headers, payload, resolved_model,
            )
        except OpenRouterCreditExhausted as exc:
            local = await self._local_fallback_async(payload, exc)
            if local is not None:
                return local
            raise
        content = data["choices"][0]["message"]["content"]
        record_usage(
            data=data,
            agent_id=agent_id,
            model=actual_model,
            method_name=method_name,
        )
        store_cache(
            self._settings,
            system=system,
            messages=messages,
            model=actual_model,
            content=content,
            temperature=temperature,
            use_cache=use_cache,
        )
        return content
