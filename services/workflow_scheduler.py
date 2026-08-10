"""Scheduled Company OS jobs — autonomous ops (CEO keeps product decisions)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _notify_ops(message: str) -> None:
    try:
        from skills.skill_telegram_notify import notify_telegram

        notify_telegram(message[:4000])
    except Exception as exc:
        logger.debug("workflow_scheduler notify failed: %s", exc)


def run_scheduled_ops(*, auto_remediate: bool = True) -> dict[str, Any]:
    """Mon–Fri ops scan + optional auto GitHub issues for open errors."""
    from services.workflow_engine import run_workflow

    result = run_workflow(
        "run_ops",
        {"auto_remediate": auto_remediate, "branch": None},
    )
    summary = result.get("summary", "")
    if auto_remediate:
        remediate = next(
            (s for s in result.get("steps", []) if s.get("step_id") == "remediate_errors"),
            None,
        )
        if remediate and remediate.get("result", {}).get("count", 0) > 0:
            summary += f" · {remediate['result']['count']} issue(s) auto-créée(s)"

    if summary:
        status = "OK" if result.get("success") else "ECART"
        _notify_ops(f"Ops ALNUA [{status}]\n{summary}")
    return result


def run_scheduled_semaine(*, weekly_plan: bool = True) -> dict[str, Any]:
    """Friday wrap-up: briefing + ops + CEO queue reminder (not decisions)."""
    from services.workflow_engine import run_workflow

    result = run_workflow("semaine", {"weekly_plan": weekly_plan})
    headline = result.get("summary") or "Brief hebdo"
    _notify_ops(f"Semaine ALNUA\n{headline}")
    return result


def run_scheduled_idle_plan(*, autonomy_level: int = 1) -> dict[str, Any]:
    """Morning idle file of the day (DEC-021)."""
    from services.workflow_engine import run_workflow

    try:
        from config.settings import settings

        if not getattr(settings, "idle_work_enabled", True):
            return {"success": False, "skipped": True, "reason": "IDLE_WORK_ENABLED=0"}
    except Exception:
        pass
    return run_workflow("idle_plan_day", {"autonomy_level": autonomy_level})


def run_scheduled_idle_drain() -> dict[str, Any]:
    """Periodic idle drain — L0–L1 free; L2 needs CEO-validated day file."""
    from services.workflow_engine import run_workflow

    try:
        from config.settings import settings

        if not getattr(settings, "idle_work_enabled", True):
            return {"success": False, "skipped": True, "reason": "IDLE_WORK_ENABLED=0"}
        autonomy = int(getattr(settings, "idle_default_autonomy_level", 1) or 1)
    except Exception:
        autonomy = 1
    return run_workflow("idle_drain", {"autonomy_level": autonomy})
