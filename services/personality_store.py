"""Persist and load tenant personality from Supabase."""

from __future__ import annotations

import logging
from typing import Any

from agents.personalities import PersonalityOverrides, set_personality

logger = logging.getLogger(__name__)


def load_personality_from_db(tenant_id: str) -> PersonalityOverrides | None:
    try:
        from database.supabase_client import get_supabase
        db = get_supabase()
        rows = db.select("tenant_personality", filters={"tenant_id": tenant_id}, limit=1)
        if not rows:
            return None
        row = rows[0]
        overrides = PersonalityOverrides(
            tone=row.get("tone", "balanced"),
            vocabulary=row.get("vocabulary", "business"),
            emoji=bool(row.get("emoji", False)),
            response_length=int(row.get("response_length", 800)),
        )
        set_personality(tenant_id, overrides)
        return overrides
    except Exception as exc:
        logger.debug("Personality DB load skipped: %s", exc)
        return None


def save_personality_to_db(tenant_id: str, overrides: PersonalityOverrides) -> dict[str, Any] | None:
    try:
        from database.supabase_client import get_supabase
        db = get_supabase()
        existing = db.select("tenant_personality", filters={"tenant_id": tenant_id}, limit=1)
        payload = {
            "tenant_id": tenant_id,
            "tone": overrides.tone,
            "vocabulary": overrides.vocabulary,
            "emoji": overrides.emoji,
            "response_length": overrides.response_length,
        }
        if existing:
            return db.update("tenant_personality", existing[0]["tenant_id"], payload, id_column="tenant_id")
        return db.insert("tenant_personality", payload)
    except Exception as exc:
        logger.warning("Personality DB save failed: %s", exc)
        return None
