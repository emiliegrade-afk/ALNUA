"""CreatorFlow — LLM calls with user BYOK or Hub fallback."""

from __future__ import annotations

import logging
from typing import Any

import httpx

from config.settings import get_settings
from database.creatorflow_supabase_client import get_cf_supabase
from services.creatorflow_secrets import decrypt_user_secret

logger = logging.getLogger(__name__)

_CF_AI_SETTINGS = "cf_user_ai_settings"


def resolve_cf_openrouter_key(user_id: str) -> tuple[str, bool]:
    """Return (api_key, is_user_key)."""
    settings = get_settings()
    db = get_cf_supabase()
    rows = db.select(_CF_AI_SETTINGS, filters={"user_id": user_id}, limit=1)
    if rows and rows[0].get("use_own_key") and rows[0].get("api_key_encrypted"):
        try:
            return decrypt_user_secret(user_id, rows[0]["api_key_encrypted"]), True
        except Exception as exc:
            logger.warning("cf BYOK decrypt failed for %s: %s", user_id[:8], exc)
    return settings.openrouter_api_key.strip(), False


def resolve_cf_model(user_id: str, fallback: str = "openai/gpt-4o-mini") -> str:
    db = get_cf_supabase()
    rows = db.select(_CF_AI_SETTINGS, filters={"user_id": user_id}, limit=1)
    if rows and rows[0].get("default_model"):
        return str(rows[0]["default_model"]).strip()
    return fallback


def cf_llm_chat(
    user_id: str,
    system: str,
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    temperature: float = 0.5,
    max_tokens: int = 4096,
) -> str:
    settings = get_settings()
    api_key, _ = resolve_cf_openrouter_key(user_id)
    if not api_key:
        raise ValueError("Aucune clé OpenRouter configurée (Hub ou BYOK)")

    resolved_model = model or resolve_cf_model(user_id)
    payload: dict[str, Any] = {
        "model": resolved_model,
        "messages": [{"role": "system", "content": system}, *messages],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://creatorflow.alnua.local",
        "X-Title": "CreatorFlow",
    }
    with httpx.Client(timeout=120.0) as client:
        response = client.post(
            f"{settings.openrouter_base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
    return str(data["choices"][0]["message"]["content"])
