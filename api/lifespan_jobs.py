"""Scheduled job runners for FastAPI lifespan."""

from __future__ import annotations

from api.route_common import *  # noqa: F403


def run_scheduled_daily_briefing() -> None:
    try:
        from datetime import date as date_cls

        from services.orchestration import run_secretary_morning_notify

        weekly = date_cls.today().weekday() == 0
        result = run_secretary_morning_notify(weekly_plan=weekly)
        logger.info(
            "Briefing matinal Nadia (weekly=%s, telegram=%s)",
            weekly,
            (result.get("notifications") or {}).get("telegram"),
        )
    except Exception:
        logger.exception("Scheduled daily briefing failed")


def run_partnership_followup_reminders_job() -> None:
    try:
        count = run_partnership_followup_reminders()
        logger.info("Partnership follow-up reminders: %s ticket(s) created", count)
    except Exception:
        logger.exception("Partnership follow-up reminder job failed")


def run_academy_poll_quiet() -> None:
    try:
        from services.orchestration import run_academy_poll_orchestration

        result = run_academy_poll_orchestration(notify=False, mark_ready_count=2)
        sync = result.get("sync") or {}
        closed = (sync.get("closed_issues") or {}).get("closed_count", 0)
        queued = (result.get("queued") or {}).get("marked_count", 0)
        logger.info(
            "Academy poll (scheduler): closed=%s queued=%s gate=%s%%",
            closed,
            queued,
            (result.get("gate") or {}).get("readiness_pct"),
        )
    except Exception:
        logger.exception("Scheduled academy poll failed")


def run_scheduled_ops_quiet() -> None:
    try:
        from services.workflow_scheduler import run_scheduled_ops

        run_scheduled_ops(auto_remediate=True)
    except Exception:
        logger.exception("Scheduled run_ops failed")


def run_scheduled_semaine_quiet() -> None:
    try:
        from services.workflow_scheduler import run_scheduled_semaine

        run_scheduled_semaine(weekly_plan=True)
    except Exception:
        logger.exception("Scheduled semaine failed")


def run_scheduled_idle_plan_quiet() -> None:
    try:
        from services.workflow_scheduler import run_scheduled_idle_plan

        result = run_scheduled_idle_plan()
        logger.info(
            "Idle plan day: success=%s summary=%s",
            result.get("success"),
            (result.get("summary") or result.get("reason") or "")[:120],
        )
    except Exception:
        logger.exception("Scheduled idle_plan_day failed")


def run_scheduled_idle_drain_quiet() -> None:
    try:
        from services.workflow_scheduler import run_scheduled_idle_drain

        result = run_scheduled_idle_drain()
        logger.info(
            "Idle drain: success=%s summary=%s",
            result.get("success"),
            (result.get("summary") or result.get("reason") or "")[:120],
        )
    except Exception:
        logger.exception("Scheduled idle_drain failed")


def run_scheduled_security_patrol() -> None:
    """Security Sentinel — patrouille Hub (pas Sentry)."""
    try:
        from services.security_sentinel import run_patrol

        report = run_patrol(notify=True)
        logger.info(
            "Security patrol: ok=%s findings=%s lockdown=%s",
            report.get("ok"),
            len(report.get("findings") or []),
            report.get("lockdown"),
        )
    except Exception:
        logger.exception("Security patrol failed")


def run_scheduled_backup() -> None:
    try:
        from services.rq_queue import enqueue_task, job_backup_daily

        job_id = enqueue_task(job_backup_daily)
        if job_id:
            logger.info("Daily backup enqueued — job_id=%s", job_id)
        else:
            from scripts.backup_daily import main as backup_main

            backup_main()
            logger.info("Daily backup completed (sync fallback)")
    except Exception:
        logger.exception("Scheduled backup failed")
