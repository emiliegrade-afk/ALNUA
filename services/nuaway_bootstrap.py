"""NUAWAY ops bootstrap — Phase 7 mise en route post-gate."""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


def _next_steps(
    gate: dict[str, Any],
    beta: dict[str, Any],
    *,
    nomad_local: bool,
    claude_ok: bool,
    gh_ok: bool,
) -> list[dict[str, str]]:
    steps: list[dict[str, str]] = []

    if not nomad_local:
        steps.append(
            {
                "id": "clone_nomad",
                "priority": "P0",
                "action": "Cloner NUAWAY : .\\scripts\\setup_nomad.ps1",
            }
        )
    if not claude_ok:
        steps.append(
            {
                "id": "claude_cli",
                "priority": "P0",
                "action": "Installer Claude Code CLI : npm i -g @anthropic-ai/claude-code",
            }
        )
    if not gh_ok:
        steps.append(
            {
                "id": "gh_auth",
                "priority": "P0",
                "action": "Authentifier gh CLI : gh auth login",
            }
        )

    for label in beta.get("missing_critical") or []:
        if "académie" in label.lower() or "n4" in label.lower():
            steps.append(
                {
                    "id": "academy_sprint",
                    "priority": "P1",
                    "action": "Lancer sprint académie : POST /orchestration/academy-sprint",
                }
            )
            break

    for label in beta.get("missing_critical") or []:
        if "sentry" in label.lower():
            steps.append(
                {
                    "id": "sentry_simulate",
                    "priority": "P1",
                    "action": "Tester pipeline Sentry : .\\scripts\\simulate_sentry.ps1",
                }
            )
            break

    if gate.get("gate_open") and not beta.get("beta_ready"):
        steps.append(
            {
                "id": "beta_checklist",
                "priority": "P1",
                "action": "Compléter checklist beta sur /hub puis Go beta CEO",
            }
        )

    if beta.get("beta_ready"):
        steps.append(
            {
                "id": "launch_beta",
                "priority": "P0",
                "action": "NUAWAY beta-ready — polish UX puis déploiement staging EAS",
            }
        )

    if not steps:
        steps.append(
            {
                "id": "monitor",
                "priority": "P2",
                "action": "Surveiller /hub 10 min/jour — laisser la boucle agents tourner",
            }
        )

    # Dedupe by id
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for s in steps:
        if s["id"] in seen:
            continue
        seen.add(s["id"])
        unique.append(s)
    return unique[:6]


def run_nuaway_bootstrap(*, refresh: bool = True) -> dict[str, Any]:
    """
    Diagnostic + prochaines actions pour passer en mode ops NUAWAY.
    """
    from shutil import which

    from services.nuaway_readiness import evaluate_beta_readiness, generate_readiness_report

    gate_block: dict[str, Any] = {}
    beta: dict[str, Any] = {}
    try:
        if refresh:
            report = generate_readiness_report(refresh_gate=True)
            beta = report
            gate_block = report.get("agents_gate") or {}
        else:
            beta = evaluate_beta_readiness(refresh_gate=False)
            gate_block = beta.get("agents_gate") or {}
    except Exception as exc:
        logger.warning("bootstrap readiness failed: %s", exc)
        beta = {"error": str(exc)[:200]}

    nomad_local = False
    nomad_path: str | None = None
    try:
        from config.github_repos import get_target_by_slug

        target = get_target_by_slug("nomad")
        if target:
            nomad_path = str(target.local_path)
            nomad_local = target.local_path.is_dir()
    except Exception:
        raw = os.getenv("REPO_PATH_NOMAD", "").strip()
        if raw:
            nomad_path = raw
            nomad_local = os.path.isdir(raw)

    claude_ok = which("claude") is not None
    gh_ok = which("gh") is not None
    api_port = os.getenv("API_PORT", "8000")

    next_steps = _next_steps(
        gate_block,
        beta,
        nomad_local=nomad_local,
        claude_ok=claude_ok,
        gh_ok=gh_ok,
    )

    if beta.get("beta_ready"):
        headline = "Bootstrap OK — NUAWAY beta-ready, mode ops agents."
    elif beta.get("missing_critical"):
        headline = f"Bootstrap — bloquant : {beta['missing_critical'][0]}"
    else:
        headline = f"Bootstrap — readiness beta {beta.get('readiness_pct', 0)}%"

    return {
        "headline": headline,
        "beta_ready": bool(beta.get("beta_ready")),
        "gate_open": bool(gate_block.get("gate_open")),
        "readiness_pct": beta.get("readiness_pct", 0),
        "missing_critical": beta.get("missing_critical") or [],
        "next_steps": next_steps,
        "environment": {
            "nomad_repo": os.getenv("GITHUB_REPO_NOMAD", "").strip() or None,
            "nomad_local_path": nomad_path,
            "nomad_cloned": nomad_local,
            "claude_cli": claude_ok,
            "gh_cli": gh_ok,
            "hub_api_port": api_port,
            "academy_repo": os.getenv("GITHUB_REPO_ACADEMY", "").strip() or None,
        },
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
