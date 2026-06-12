"""
skill_error_journal.py

Persistent error journal for ALNUA agents.
Used by: DevAppAgent, DevGamingAgent, EmbeddedDevAgent, R&DAgent
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def _get_db():
    from database.supabase_client import get_supabase

    return get_supabase()


def log_error(
    agent_name: str,
    error_type: str,
    error_message: str,
    context: str | None = None,
    task_id: str | None = None,
) -> str | None:
    """Log a new error entry. Returns the created row ID."""
    try:
        row = _get_db().insert(
            "agent_error_journal",
            {
                "agent_name": agent_name,
                "task_id": task_id,
                "error_type": error_type,
                "error_message": error_message[:2000],
                "context": context[:1000] if context else None,
                "status": "open",
            },
        )
        entry_id = row["id"]
        logger.info("[ErrorJournal] Logged %s (ID: %s)", error_type, entry_id)
        return entry_id
    except Exception as exc:
        logger.warning("[ErrorJournal] Failed to log error: %s", exc)
        return None


def search_similar_errors(
    agent_name: str,
    error_message: str,
    error_type: str | None = None,
    limit: int = 3,
) -> list[dict[str, Any]]:
    """
    Search resolved errors with known solutions.
    Priority: same agent + same type + similar message.
    """
    try:
        db = _get_db()
        query = (
            db.raw.table("agent_error_journal")
            .select("error_type, error_message, context, solution, attempts")
            .eq("status", "resolved")
            .eq("agent_name", agent_name)
        )
        if error_type:
            query = query.eq("error_type", error_type)

        keywords = " ".join(error_message.split()[:10])
        results = query.ilike("error_message", f"%{keywords[:50]}%").limit(limit).execute()

        if results.data:
            return results.data

        fallback = (
            db.raw.table("agent_error_journal")
            .select("agent_name, error_type, error_message, solution")
            .eq("status", "resolved")
            .eq("error_type", error_type or "unknown")
            .limit(limit)
            .execute()
        )
        return fallback.data or []

    except Exception as exc:
        logger.warning("[ErrorJournal] Search failed: %s", exc)
        return []


def mark_resolved(entry_id: str, solution: str) -> None:
    """Mark an error as resolved with the working solution."""
    try:
        _get_db().update(
            "agent_error_journal",
            entry_id,
            {
                "status": "resolved",
                "solution": solution[:2000],
                "resolved_at": datetime.now(timezone.utc).isoformat(),
            },
        )
        logger.info("[ErrorJournal] Entry %s marked resolved", entry_id)
    except Exception as exc:
        logger.warning("[ErrorJournal] Failed to mark resolved: %s", exc)


def mark_escalated(entry_id: str) -> None:
    """Mark an error as escalated to the COO."""
    try:
        _get_db().update("agent_error_journal", entry_id, {"status": "escalated"})
    except Exception as exc:
        logger.warning("[ErrorJournal] Failed to mark escalated: %s", exc)


def increment_attempts(entry_id: str) -> None:
    """Atomically increment the attempt counter via RPC."""
    try:
        _get_db().raw.rpc("increment_error_attempts", {"entry_id": entry_id}).execute()
    except Exception as exc:
        logger.warning("[ErrorJournal] Failed to increment attempts: %s", exc)


def build_retry_context(similar_errors: list[dict[str, Any]]) -> str:
    """Build learning context from past errors for retry prompts."""
    if not similar_errors:
        return ""

    lines = ["\n⚠️ APPRENTISSAGE — Erreurs similaires déjà rencontrées :\n"]
    for i, err in enumerate(similar_errors, 1):
        lines.append(f"Erreur #{i} ({err.get('error_type', '?')}) :")
        lines.append(f"  Problème : {err.get('error_message', '?')[:200]}")
        if err.get("solution"):
            lines.append(f"  [OK] Solution qui a fonctionné : {err['solution'][:300]}")
        lines.append("")

    lines.append("→ Tiens compte de ces expériences passées pour éviter les mêmes erreurs.\n")
    return "\n".join(lines)


def get_open_errors_summary(agent_name: str | None = None) -> str:
    """Return a summary of unresolved errors for the COO morning brief."""
    try:
        db = _get_db()
        query = (
            db.raw.table("agent_error_journal")
            .select("agent_name, error_type, task_id, attempts, created_at")
            .in_("status", ["open", "escalated"])
        )
        if agent_name:
            query = query.eq("agent_name", agent_name)

        results = query.order("created_at", desc=True).limit(10).execute()

        if not results.data:
            return "[OK] Aucune erreur ouverte dans le journal."

        lines = [f"⚠️ {len(results.data)} erreur(s) non résolue(s) :"]
        for err in results.data:
            lines.append(
                f"• [{err['agent_name']}] {err['error_type']} "
                f"(tâche: {err.get('task_id', '?')}, {err['attempts']} tentative(s))"
            )
        return "\n".join(lines)

    except Exception as exc:
        return f"[ERREUR] Erreur lecture journal : {exc}"
