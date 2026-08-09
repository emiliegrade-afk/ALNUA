"""R&D Center — LLM / OpenRouter helpers."""
from __future__ import annotations

import json
import logging
import os
import urllib.request
from typing import Any

logger = logging.getLogger("rnd_center")

OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"


def _rnd_model() -> str:
    """Prefer a JSON-reliable model; minimax-m1 often returns reasoning-only text."""
    from agents.base import resolve_openrouter_model, to_api_model_slug

    env_override = os.getenv("RND_MODEL", "").strip()
    if env_override:
        return to_api_model_slug(env_override)
    return resolve_openrouter_model("rnd_agent")


def _extract_message_text(message: dict[str, Any]) -> str:
    """OpenRouter reasoning models may leave content null and use reasoning fields."""
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()

    reasoning = message.get("reasoning")
    if isinstance(reasoning, str) and reasoning.strip():
        return reasoning.strip()

    parts: list[str] = []
    for detail in message.get("reasoning_details") or []:
        if isinstance(detail, dict) and detail.get("text"):
            parts.append(str(detail["text"]))
    return "\n".join(parts).strip()


def _openrouter_key() -> str:
    from config.settings import get_settings

    return get_settings().openrouter_api_key.strip()


def _llm(system: str, user: str, model: str | None = None, max_tokens: int = 4000) -> str:
    api_key = _openrouter_key()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY manquante dans .env")

    model_slug = (model or _rnd_model()).replace("openrouter/", "")

    payload = json.dumps({
        "model": model_slug,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.8,  # Plus élevé pour la créativité R&D
        "max_tokens": max_tokens,
        "session_id": "alnua:rnd_center",
        "cache_control": {"type": "ephemeral", "ttl": "1h"},
    }).encode()
    req = urllib.request.Request(
        OPENROUTER_BASE,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Session-Id": "alnua:rnd_center",
            "X-Title": "ALNUA Hub R&D",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read())
    message = data["choices"][0]["message"]
    text = _extract_message_text(message)
    if not text:
        raise RuntimeError(f"Réponse LLM vide (model={model_slug})")
    return text
