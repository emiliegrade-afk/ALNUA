"""CEO cockpit aggregator — Phase 5 dashboard data."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def get_ceo_cockpit() -> dict[str, Any]:
    """Single payload for CEO /hub cockpit."""
    gate: dict[str, Any] = {}
    academy: dict[str, Any] = {}
    production: dict[str, Any] = {}
    ceo_queue: dict[str, Any] = {"to_validate": [], "to_prepare": []}
    pipeline_issues = 0

    try:
        from services.academy_gate import evaluate_academy_gate

        gate = evaluate_academy_gate(refresh_academy=True)
    except Exception as exc:
        gate = {"error": str(exc)[:200]}
        logger.warning("academy gate failed: %s", exc)

    try:
        from services.academy_progress import get_academy_status

        academy = get_academy_status()
    except Exception as exc:
        academy = {"error": str(exc)[:200]}

    try:
        from services.production_ops import get_production_ops_status

        production = get_production_ops_status()
    except Exception as exc:
        production = {"error": str(exc)[:200]}

    try:
        from agents.rnd_ceo_agent import RndCeoAgent

        ceo_queue = RndCeoAgent().list_ceo_queue(limit=8)
    except Exception as exc:
        ceo_queue = {"error": str(exc)[:200]}

    try:
        from skills.skill_gh_issues import list_ready_issues

        issues = list_ready_issues()
        pipeline_issues = len(issues) if issues else 0
    except Exception:
        pipeline_issues = 0

    headline = _build_headline(gate, ceo_queue, pipeline_issues)

    return {
        "headline": headline,
        "academy_gate": gate,
        "academy": academy,
        "production_ops": production,
        "ceo_queue": ceo_queue,
        "pipeline": {
            "agent_ready_count": pipeline_issues,
            "github_configured": bool(os.getenv("GITHUB_TOKEN", "").strip()),
        },
    }


def _build_headline(
    gate: dict[str, Any],
    ceo_queue: dict[str, Any],
    pipeline_issues: int,
) -> str:
    if gate.get("gate_open"):
        return "Gate Academy ouverte — dev_app prêt pour Lounge."

    pct = gate.get("readiness_pct", 0)
    pending = len((ceo_queue or {}).get("to_validate") or [])
    parts = [f"Readiness Academy {pct}%"]

    if pending:
        parts.append(f"{pending} dossier(s) CEO à valider")
    if pipeline_issues:
        parts.append(f"{pipeline_issues} issue(s) agent-ready")

    missing = [
        c["label"]
        for c in (gate.get("criteria") or [])
        if c.get("critical") and not c.get("passed")
    ]
    if missing:
        parts.append(f"bloquant : {missing[0]}")

    return " — ".join(parts)
