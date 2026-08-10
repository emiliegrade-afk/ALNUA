"""Shared input sanitization for agents_pole routers."""

from __future__ import annotations

from services.input_sanitizer import sanitize_user_input


def clean_agent_text(text: str, *, max_length: int = 6000) -> str:
    """Bound + strip prompt-injection patterns from free text headed for an LLM.

    PII redaction stays off here: these endpoints routinely carry real business
    data (client emails, phone numbers in contracts) that must reach the agent
    intact — unlike the Telegram chat surface, which redacts by default.
    """
    return sanitize_user_input(text, max_length=max_length, redact_pii_enabled=False)
