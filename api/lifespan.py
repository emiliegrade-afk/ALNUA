"""FastAPI lifespan — fast /health first, heavy jobs deferred."""

from __future__ import annotations

import time
from zoneinfo import ZoneInfo

from api.route_common import *  # noqa: F403

_briefing_scheduler: BackgroundScheduler | None = None
_background_started = False


def _scheduler_timezone(settings: Any) -> ZoneInfo:
    try:
        return ZoneInfo(settings.scheduler_timezone)
    except Exception:
        logger.warning(
            "Invalid SCHEDULER_TIMEZONE=%r - falling back to Europe/Paris",
            settings.scheduler_timezone,
        )
        return ZoneInfo("Europe/Paris")


def _run_scheduled_daily_briefing() -> None:
    try:
        from services.orchestration import run_secretary_morning_notify
        from datetime import date as date_cls

        weekly = date_cls.today().weekday() == 0
        result = run_secretary_morning_notify(weekly_plan=weekly)
        logger.info(
            "Briefing matinal Nadia (weekly=%s, telegram=%s)",
            weekly,
            (result.get("notifications") or {}).get("telegram"),
        )
    except Exception:
        logger.exception("Scheduled daily briefing failed")


def _run_partnership_followup_reminders() -> None:
    try:
        count = run_partnership_followup_reminders()
        logger.info("Partnership follow-up reminders: %s ticket(s) created", count)
    except Exception:
        logger.exception("Partnership follow-up reminder job failed")


def _run_academy_poll_quiet() -> None:
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


def _init_fast(settings: Any) -> None:
    """Minimal sync init so /health responds quickly."""
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)
        logger.info("Sentry initialized")
    try:
        from services.cli_paths import ensure_coding_cli_path

        ensure_coding_cli_path()
    except Exception:
        pass
    try:
        ensure_brand_kit_dirs()
    except Exception:
        logger.exception("Could not initialize brand_kits directories")
    try:
        ensure_contract_dirs()
    except Exception:
        logger.exception("Could not initialize contract directories")
    try:
        from services.otel import setup_otel
        setup_otel()
    except Exception:
        pass
    try:
        from services.personality_store import load_personality_from_db
        from models.tenant import DEFAULT_TENANT_ID
        load_personality_from_db(DEFAULT_TENANT_ID)
    except Exception:
        pass


def _run_scheduled_ops_quiet() -> None:
    try:
        from services.workflow_scheduler import run_scheduled_ops

        run_scheduled_ops(auto_remediate=True)
    except Exception:
        logger.exception("Scheduled run_ops failed")


def _run_scheduled_semaine_quiet() -> None:
    try:
        from services.workflow_scheduler import run_scheduled_semaine

        run_scheduled_semaine(weekly_plan=True)
    except Exception:
        logger.exception("Scheduled semaine failed")


def _run_scheduled_backup() -> None:
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


async def _start_background_services(settings: Any) -> None:
    """Heavy subsystems — run after server accepts HTTP (hub_fast_start)."""
    global _briefing_scheduler, _background_started
    if _background_started:
        return
    _background_started = True

    delay = 8 if settings.hub_fast_start else 0
    if delay:
        logger.info("Background services in %ss (HUB_FAST_START)", delay)
        await asyncio.sleep(delay)

    cron_tz = _scheduler_timezone(settings)
    if settings.scheduler_leader:
        _briefing_scheduler = BackgroundScheduler(timezone=cron_tz)
        _briefing_scheduler.add_job(
            _run_scheduled_daily_briefing,
            CronTrigger(hour=8, minute=0, timezone=cron_tz),
            id="daily_briefing",
            replace_existing=True,
        )
        _briefing_scheduler.add_job(
            _run_partnership_followup_reminders,
            CronTrigger(hour=8, minute=5, timezone=cron_tz),
            id="partnership_followups",
            replace_existing=True,
        )
        _briefing_scheduler.add_job(
            _run_academy_poll_quiet,
            "interval",
            minutes=20,
            id="academy_poll_quiet",
            replace_existing=True,
        )
        _briefing_scheduler.add_job(
            _run_scheduled_ops_quiet,
            CronTrigger(hour=8, minute=15, day_of_week="mon-fri", timezone=cron_tz),
            id="company_ops_run",
            replace_existing=True,
        )
        _briefing_scheduler.add_job(
            _run_scheduled_semaine_quiet,
            CronTrigger(hour=17, minute=0, day_of_week="fri", timezone=cron_tz),
            id="company_semaine",
            replace_existing=True,
        )
        _briefing_scheduler.add_job(
            _run_scheduled_backup,
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
        import threading

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
        import threading

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

    # Telegram in-process only if explicitly enabled (external bots via start-all.ps1)
    if settings.telegram_bot_token and settings.telegram_polling:
        import threading

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
        import threading

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


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    _init_fast(settings)

    bg_task = asyncio.create_task(_start_background_services(settings))

    yield

    bg_task.cancel()
    try:
        await bg_task
    except asyncio.CancelledError:
        pass

    try:
        from agents.bug_watchdog import stop_watchdog

        stop_watchdog()
    except Exception:
        logger.exception("BugWatchdog shutdown failed")

    if settings.telegram_bot_token:
        try:
            await get_telegram_bot().shutdown()
        except Exception:
            logger.exception("Telegram COO bot shutdown failed")

    if settings.telegram_secretary_bot_token:
        try:
            from bots.telegram_secretary_bot import get_telegram_secretary_bot

            await get_telegram_secretary_bot().shutdown()
        except Exception:
            logger.exception("Telegram Nadia bot shutdown failed")

    global _briefing_scheduler
    if _briefing_scheduler:
        _briefing_scheduler.shutdown(wait=False)
        _briefing_scheduler = None
