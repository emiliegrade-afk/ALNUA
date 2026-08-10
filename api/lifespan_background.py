"""Background service startup for FastAPI lifespan."""

from __future__ import annotations

import asyncio
import threading
import time
from typing import Any

from api.lifespan_init import scheduler_timezone
from api.lifespan_jobs import (
    run_academy_poll_quiet,
    run_partnership_followup_reminders_job,
    run_scheduled_backup,
    run_scheduled_daily_briefing,
    run_scheduled_ops_quiet,
    run_scheduled_semaine_quiet,
)
from api.route_common import *  # noqa: F403

_briefing_scheduler: BackgroundScheduler | None = None
_background_started = False


def get_briefing_scheduler() -> BackgroundScheduler | None:
    return _briefing_scheduler


def shutdown_briefing_scheduler() -> None:
    global _briefing_scheduler
    if _briefing_scheduler:
        _briefing_scheduler.shutdown(wait=False)
        _briefing_scheduler = None


async def start_background_services(settings: Any) -> None:
    """Heavy subsystems — run after server accepts HTTP (hub_fast_start)."""
    global _briefing_scheduler, _background_started
    if _background_started:
        return
    _background_started = True

    delay = 8 if settings.hub_fast_start else 0
    if delay:
        logger.info("Background services in %ss (HUB_FAST_START)", delay)
        await asyncio.sleep(delay)

    cron_tz = scheduler_timezone(settings)
    if settings.scheduler_leader:
        _briefing_scheduler = BackgroundScheduler(timezone=cron_tz)
        _briefing_scheduler.add_job(
            run_scheduled_daily_briefing,
            CronTrigger(hour=8, minute=0, timezone=cron_tz),
            id="daily_briefing",
            replace_existing=True,
        )
        _briefing_scheduler.add_job(
            run_partnership_followup_reminders_job,
            CronTrigger(hour=8, minute=5, timezone=cron_tz),
            id="partnership_followups",
            replace_existing=True,
        )
        _briefing_scheduler.add_job(
            run_academy_poll_quiet,
            "interval",
            minutes=20,
            id="academy_poll_quiet",
            replace_existing=True,
        )
        _briefing_scheduler.add_job(
            run_scheduled_ops_quiet,
            CronTrigger(hour=8, minute=15, day_of_week="mon-fri", timezone=cron_tz),
            id="company_ops_run",
            replace_existing=True,
        )
        _briefing_scheduler.add_job(
            run_scheduled_semaine_quiet,
            CronTrigger(hour=17, minute=0, day_of_week="fri", timezone=cron_tz),
            id="company_semaine",
            replace_existing=True,
        )
        _briefing_scheduler.add_job(
            run_scheduled_backup,
            CronTrigger(hour=3, minute=0, timezone=cron_tz),
            id="daily_backup",
            replace_existing=True,
        )
        _briefing_scheduler.start()
        logger.info("Scheduler started (08:00 %s)", cron_tz.key)
    else:
        logger.info("Scheduler skipped (SCHEDULER_LEADER=0)")

    from config.github_repos import pipeline_enabled

    if pipeline_enabled():
        try:
            from services.coding_learning import bootstrap_academy_lessons

            n = bootstrap_academy_lessons()
            if n:
                logger.info("Academy coding lessons bootstrapped: %d", n)
        except Exception:
            logger.exception("Academy lesson bootstrap skipped")
        await asyncio.sleep(2)
        asyncio.create_task(poll_issues_loop())
        logger.info("GitHub Issues polling started")
    else:
        logger.warning("GitHub Issues polling disabled")

    try:
        from agents.project_scanner import scan_all_projects

        def _delayed_scan() -> None:
            time.sleep(300)
            scan_all_projects()

        threading.Thread(target=_delayed_scan, daemon=True, name="project-scanner-delay").start()
        if _briefing_scheduler is not None:
            _briefing_scheduler.add_job(
                scan_all_projects,
                "interval",
                hours=6,
                id="project_scanner",
                replace_existing=True,
            )
        logger.info("ProjectScanner: first scan in 5min, then every 6h")
    except Exception:
        logger.exception("ProjectScanner: impossible de demarrer")

    try:
        from agents.bug_watchdog import start_watchdog

        start_watchdog()
        logger.info("BugWatchdog started")
    except Exception:
        logger.exception("BugWatchdog: impossible de demarrer")

    try:
        from skills.skill_web_research import research_all_agents

        def _delayed_research() -> None:
            time.sleep(600)
            research_all_agents(blocking=False)

        threading.Thread(target=_delayed_research, daemon=True, name="web-research-delay").start()
        if _briefing_scheduler is not None:
            _briefing_scheduler.add_job(
                research_all_agents,
                CronTrigger(day_of_week="mon", hour=7, minute=0, timezone=cron_tz),
                id="weekly_research",
                replace_existing=True,
            )
    except Exception:
        logger.exception("Veille web: impossible de demarrer")

    try:
        from agents.rnd_center import run_rnd_cycle

        if _briefing_scheduler is not None:
            _briefing_scheduler.add_job(
                lambda: run_rnd_cycle(blocking=False),
                CronTrigger(day_of_week="fri", hour=18, minute=0, timezone=cron_tz),
                id="weekly_rnd",
                replace_existing=True,
            )
    except Exception:
        logger.exception("Centre R&D: impossible de planifier")

    try:
        from services.orchestration import run_content_sprint

        if _briefing_scheduler is not None:
            _briefing_scheduler.add_job(
                lambda: run_content_sprint(
                    brief="Retrospective ALNUA — temps forts, livrables, prochaines etapes.",
                    platforms=["linkedin", "discord"],
                ),
                CronTrigger(day_of_week="fri", hour=17, minute=0, timezone=cron_tz),
                id="weekly_content_sprint",
                replace_existing=True,
            )
    except Exception:
        logger.exception("Sprint contenu: impossible de planifier")

    if settings.telegram_bot_token and settings.telegram_polling:

        def _telegram_polling_loop() -> None:
            try:
                get_telegram_bot().run_polling()
            except Exception:
                logger.exception("Telegram COO polling thread crashed")

        threading.Thread(
            target=_telegram_polling_loop,
            name="telegram-coo-polling",
            daemon=True,
        ).start()

    if settings.telegram_secretary_bot_token and settings.telegram_secretary_polling:

        def _secretary_polling_loop() -> None:
            try:
                from bots.telegram_secretary_bot import get_telegram_secretary_bot

                get_telegram_secretary_bot().run_polling()
            except Exception:
                logger.exception("Telegram Nadia polling thread crashed")

        threading.Thread(
            target=_secretary_polling_loop,
            name="telegram-secretary-polling",
            daemon=True,
        ).start()

    logger.info("Background services ready")
