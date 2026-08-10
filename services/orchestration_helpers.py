"""Shared helpers for orchestration workflows."""

from __future__ import annotations

import logging
from typing import Any

from agents.base import log_agent_action
from database.supabase_client import get_supabase

logger = logging.getLogger(__name__)

MORNING_COO_PROMPT = """Briefing du jour — agis en COO d'ALNUA.

1. Lis le briefing quotidien (get_daily_briefing si besoin).
2. Identifie les 3 priorités du jour (tickets ouverts, deadlines, alertes).
3. Pour chaque priorité : nomme l'agent responsable et l'action concrète.
4. Signale tout blocage nécessitant Emilie.

Format : plan d'action en 5 lignes max, pas de blabla."""

WEEKLY_COO_PROMPT = """Plan de la semaine — lundi matin, agis en COO d'ALNUA.

1. Synthèse des priorités de la semaine (projets Naïa / Wyrdheim / Eve / Hub).
2. Répartition des tâches par agent (pm, spec, qa, dev_app, dev_backend, marketing, content).
3. Deadlines et dépendances critiques.
4. Une recommandation pour protéger le temps d'Emilie.

Format : 8 lignes max, structuré par jour ou par projet."""


def _log_run(workflow: str, summary: str, *, success: bool = True) -> None:
    try:
        log_agent_action(
            get_supabase(),
            "coo",
            f"orchestration_{workflow}",
            input_summary=workflow,
            output_summary=summary[:200],
            status="success" if success else "error",
        )
    except Exception:
        pass


def _notify(message: str) -> dict[str, Any]:
    try:
        from skills.skill_hub_notify import notify_hub

        return notify_hub(message)
    except Exception:
        logger.exception("orchestration notify failed")
        return {"telegram": False, "discord": False}


def _resolve_project_id(
    project_id: str | None = None,
    project_slug: str | None = None,
) -> str | None:
    if project_id:
        return project_id
    db = get_supabase()
    try:
        if project_slug:
            rows = db.select("projects", filters={"slug": project_slug}, limit=1)
            if rows:
                return rows[0]["id"]
        for name in ("ALNUA", "ALNUA Hub"):
            rows = db.select("projects", filters={"name": name}, limit=1)
            if rows:
                return rows[0]["id"]
        rows = db.select("projects", limit=1)
        if rows:
            return rows[0]["id"]
    except Exception:
        pass
    return None
