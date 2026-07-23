"""Persist agent feedback to Supabase agent_feedback table."""

from __future__ import annotations

import logging
from typing import Any

from database.tenant_scope import get_current_tenant_id

logger = logging.getLogger(__name__)


def save_agent_feedback(
    *,
    agent_id: str,
    response_id: str,
    rating: int,
    comment: str | None = None,
    original_message: str | None = None,
    original_response: str | None = None,
) -> dict[str, Any] | None:
    try:
        from database.supabase_client import get_supabase
        db = get_supabase()
        return db.insert(
            "agent_feedback",
            {
                "tenant_id": get_current_tenant_id(),
                "agent_id": agent_id,
                "response_id": response_id,
                "rating": rating,
                "comment": comment,
                "original_message": (original_message or "")[:4000] or None,
                "original_response": (original_response or "")[:8000] or None,
            },
        )
    except Exception as exc:
        logger.warning("agent_feedback DB save failed: %s", exc)
        return None
