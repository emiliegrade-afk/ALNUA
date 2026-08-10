"""Academy sprint, poll, and gate orchestration workflows."""

from __future__ import annotations

import logging
from typing import Any

from services.orchestration_helpers import _log_run, _notify

logger = logging.getLogger(__name__)


def run_academy_sprint_orchestration(
    *,
    level: int | None = None,
    seed_if_missing: bool = True,
    mark_ready_count: int = 3,
) -> dict[str, Any]:
    """Seed + agent-ready pour l'académie ALNUA."""
    from services.academy_seed import run_academy_sprint

    try:
        result = run_academy_sprint(
            level=level,
            seed_if_missing=seed_if_missing,
            mark_ready_count=mark_ready_count,
        )
        marked = result.get("agent_ready", {}).get("marked_count", 0)
        _log_run("academy_sprint", f"level={level} ready={marked}")
        _notify(
            f"🎓 Sprint Académie ALNUA\n"
            f"Niveau : {level or 'auto'}\n"
            f"Issues agent-ready : {marked}"
        )
        return {**result, "success": True}
    except Exception as exc:
        logger.exception("academy_sprint failed")
        _log_run("academy_sprint", str(exc), success=False)
        _notify(f"❌ Sprint Académie échoué : {exc}")
        return {"workflow": "academy_sprint", "success": False, "error": str(exc)}


def run_academy_poll_orchestration(
    *,
    mark_ready_if_idle: bool = True,
    mark_ready_count: int = 2,
    notify: bool = True,
) -> dict[str, Any]:
    """
    Poll Academy infra: sync progress, close agent-done issues, advance level, queue next.
    Called by Hub poll_issues_loop backup + n8n workflow 12 every 30min.
    """
    from services.academy_gate import evaluate_academy_gate
    from services.academy_issue_sync import run_academy_sync

    try:
        sync = run_academy_sync()
        progress = sync.get("progress") or {}

        queued: dict[str, Any] | None = None
        if mark_ready_if_idle:
            from services.agent_wake import queue_academy_if_idle

            queued = queue_academy_if_idle(
                count=mark_ready_count if mark_ready_count > 0 else None
            )

        gate = evaluate_academy_gate(refresh_academy=False)

        summary = (
            f"L{progress.get('current_level')} "
            f"{progress.get('completed_exercises')}/{progress.get('total_exercises')} "
            f"gate={gate.get('readiness_pct')}%"
        )
        _log_run("academy_poll", summary)

        if notify:
            closed = sync.get("closed_issues", {}).get("closed_count", 0)
            ready_n = (queued or {}).get("marked_count", 0)
            msg = (
                f"🎓 Academy poll\n"
                f"Progression : {progress.get('completed_exercises')}/"
                f"{progress.get('total_exercises')} "
                f"(L{progress.get('current_level')})\n"
                f"Issues fermées : {closed} | agent-ready : {ready_n}\n"
                f"Gate readiness : {gate.get('readiness_pct')}%"
            )
            if gate.get("gate_open"):
                msg += "\n✅ GATE OUVERTE — Lounge/arcade autorisé"
            _notify(msg)

        return {
            "workflow": "academy_poll",
            "success": True,
            "sync": sync,
            "queued": queued,
            "gate": gate,
        }
    except Exception as exc:
        logger.exception("academy_poll failed")
        _log_run("academy_poll", str(exc), success=False)
        if notify:
            _notify(f"❌ Academy poll échoué : {exc}")
        return {"workflow": "academy_poll", "success": False, "error": str(exc)}


def run_academy_gate_orchestration(*, notify: bool = True) -> dict[str, Any]:
    """Évalue la gate Academy → Lounge et notifie si bloquante (n8n workflow 10)."""
    from services.academy_gate import evaluate_academy_gate

    try:
        result = evaluate_academy_gate(refresh_academy=True)
        pct = result.get("readiness_pct", 0)
        open_ = bool(result.get("gate_open"))
        _log_run("academy_gate", f"readiness={pct}% open={open_}")
        if notify:
            status = "✅ OPEN" if open_ else f"🔒 {pct}%"
            missing = [
                c["label"]
                for c in result.get("criteria", [])
                if c.get("critical") and not c.get("passed")
            ]
            msg = f"🚦 Gate Academy — {status}"
            if missing and not open_:
                msg += f"\nBloquant : {missing[0]}"
            _notify(msg)
        return {**result, "success": True, "workflow": "academy_gate"}
    except Exception as exc:
        logger.exception("academy_gate failed")
        _log_run("academy_gate", str(exc), success=False)
        if notify:
            _notify(f"❌ Évaluation gate Academy échouée : {exc}")
        return {"workflow": "academy_gate", "success": False, "error": str(exc)}
