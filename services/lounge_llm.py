"""Lounge LLM routing — cheap CN model by default (DEC-031 §7), not métier."""

from __future__ import annotations

# Competent + inexpensive Chinese models on OpenRouter (Lounge filler).
LOUNGE_DEFAULT_MODEL = "deepseek/deepseek-chat-v3.2"


def get_lounge_model() -> str:
    """
    Model for all Lounge LLM calls (puzzles, future games).

    Priority:
      1. settings.lounge_model / LOUNGE_MODEL
      2. LOUNGE_DEFAULT_MODEL (DeepSeek V3.2 — CN, cheap, capable)
    Agent métier tier is intentionally ignored.
    Cost still attributed to the playing agent_id via LLMClient.
    """
    try:
        from config.settings import settings

        override = (getattr(settings, "lounge_model", "") or "").strip()
        if override:
            return override
    except Exception:
        pass

    return LOUNGE_DEFAULT_MODEL
