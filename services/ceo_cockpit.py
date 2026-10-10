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

    trust = _trust_section()

    headline = _build_headline(gate, ceo_queue, pipeline_issues)

    return {
        "headline": headline,
        "academy_gate": gate,
        "academy": academy,
        "production_ops": production,
        "ceo_queue": ceo_queue,
        "trust": trust,
        "pipeline": {
            "agent_ready_count": pipeline_issues,
            "github_configured": bool(os.getenv("GITHUB_TOKEN", "").strip()),
        },
    }


def _next_threshold(score: float) -> float | None:
    for band in (0.70, 0.80, 0.90):
        if score < band:
            return band
    return None


def _trust_section() -> dict[str, Any]:
    """Trust → autonomy visibility (DEC-043): per-agent score, level, distance
    to the next autonomy band. Academy-sourced scores are capped at 0.85."""
    try:
        from services.agent_trust import ACADEMY_TRUST_CAP, list_trust
        from services.autonomy_resolver import trust_score_to_autonomy

        agents = []
        for row in list_trust(limit=12):
            score = float(row.get("score") or 0.0)
            history = row.get("history") or []
            agents.append(
                {
                    "agent_id": row.get("agent_id"),
                    "score": score,
                    "autonomy_level": trust_score_to_autonomy(score),
                    "samples": int(row.get("samples") or 0),
                    "successes": int(row.get("successes") or 0),
                    "failures": int(row.get("failures") or 0),
                    "next_threshold": _next_threshold(score),
                    "last_note": (history[-1].get("note", "") if history else ""),
                }
            )
        return {"agents": agents, "count": len(agents), "academy_cap": ACADEMY_TRUST_CAP}
    except Exception as exc:
        logger.warning("trust section failed: %s", exc)
        return {"agents": [], "count": 0, "error": str(exc)[:200]}


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
