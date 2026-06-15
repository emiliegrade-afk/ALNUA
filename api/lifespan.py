"""FastAPI lifespan — schedulers, bots, background tasks."""

from __future__ import annotations

from zoneinfo import ZoneInfo

from api.route_common import *  # noqa: F403

_briefing_scheduler: BackgroundScheduler | None = None


def _scheduler_timezone(settings: Any) -> ZoneInfo:
    try:
        return ZoneInfo(settings.scheduler_timezone)
    except Exception:
        logger.warning(
            "Invalid SCHEDULER_TIMEZONE=%r — falling back to Europe/Paris",
            settings.scheduler_timezone,
        )
        return ZoneInfo("Europe/Paris")


def _run_scheduled_daily_briefing() -> None:
    try:
        from services.orchestration import run_morning_orchestration
        from datetime import date as date_cls

        weekly = date_cls.today().weekday() == 0
        result = run_morning_orchestration(weekly_plan=weekly)
        logger.info(
            "Briefing matinal orchestré (weekly=%s, telegram=%s)",
            weekly,
            result.get("telegram_sent"),
        )
    except Exception:
        logger.exception("Scheduled daily briefing failed")


def _run_partnership_followup_reminders() -> None:
    try:
        count = run_partnership_followup_reminders()
        logger.info("Partnership follow-up reminders: %s ticket(s) created", count)
    except Exception:
        logger.exception("Partnership follow-up reminder job failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _briefing_scheduler
    settings = get_settings()
    if settings.sentry_dsn:
        sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1)
        logger.info("Sentry initialized")
    try:
        ensure_brand_kit_dirs()
        logger.info("Brand kit directories ready")
    except Exception:
        logger.exception("Could not initialize brand_kits directories")
    try:
        ensure_contract_dirs()
        logger.info("Partnership contract directories ready")
    except Exception:
        logger.exception("Could not initialize contract directories")

    # === SCHEDULER ===
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
        _briefing_scheduler.start()
        logger.info("Daily briefing scheduler started (08:00 %s)", cron_tz.key)
    else:
        logger.info("Scheduler skipped on this worker (SCHEDULER_LEADER=0)")

    from config.github_repos import pipeline_enabled

    if pipeline_enabled():
        asyncio.create_task(poll_issues_loop())
        logger.info("GitHub Issues polling started (multi-repo, agent-ready)")
    else:
        logger.warning(
            "GitHub Issues polling disabled — GITHUB_TOKEN or repo config missing"
        )

    # === PROJECT SCANNER — auto-discovery GitHub + fichiers locaux → Chroma + Mem0 ===
    try:
        from agents.project_scanner import scan_all_projects
        import threading
        threading.Thread(target=scan_all_projects, daemon=True).start()
        if _briefing_scheduler is not None:
            _briefing_scheduler.add_job(
                scan_all_projects,
                "interval",
                hours=6,
                id="project_scanner",
                replace_existing=True,
            )
        logger.info("ProjectScanner: démarré (scan immédiat + toutes les 6h)")
    except Exception:
        logger.exception("ProjectScanner: impossible de démarrer")

    # === BUG WATCHDOG — surveillance erreurs + auto-fix autonome ===
    try:
        from agents.bug_watchdog import start_watchdog

        start_watchdog()
        logger.info("BugWatchdog: configuré (WATCHDOG_ENABLED / poll interval via env)")
    except Exception:
        logger.exception("BugWatchdog: impossible de démarrer")

    # === VEILLE WEB — chaque agent fait sa veille dans son domaine ===
    try:
        from skills.skill_web_research import research_all_agents
        # Premier cycle au démarrage (décalé de 2min pour ne pas surcharger)
        import threading, time
        def _delayed_research():
            time.sleep(120)
            research_all_agents(blocking=False)
        threading.Thread(target=_delayed_research, daemon=True).start()
        # Puis toutes les semaines le lundi à 7h
        if _briefing_scheduler is not None:
            _briefing_scheduler.add_job(
                research_all_agents,
                CronTrigger(day_of_week="mon", hour=7, minute=0, timezone=cron_tz),
                id="weekly_research",
                replace_existing=True,
            )
        logger.info("Veille web: démarrée (cycle immédiat + lundi 07:00)")
    except Exception:
        logger.exception("Veille web: impossible de démarrer")

    # === CENTRE R&D — cycle hebdomadaire autonome ===
    try:
        from agents.rnd_center import run_rnd_cycle
        # Chaque vendredi à 18h — rapport R&D de la semaine
        if _briefing_scheduler is not None:
            _briefing_scheduler.add_job(
                lambda: run_rnd_cycle(blocking=False),
                CronTrigger(day_of_week="fri", hour=18, minute=0, timezone=cron_tz),
                id="weekly_rnd",
                replace_existing=True,
            )
        logger.info("Centre R&D: démarré (vendredi 18:00)")
    except Exception:
        logger.exception("Centre R&D: impossible de démarrer")

    # === SPRINT CONTENU — vendredi 17h ===
    try:
        from services.orchestration import run_content_sprint

        if _briefing_scheduler is not None:
            _briefing_scheduler.add_job(
                lambda: run_content_sprint(
                    brief="Rétrospective de la semaine ALNUA — temps forts, livrables, prochaines étapes.",
                    platforms=["linkedin", "discord"],
                ),
                CronTrigger(day_of_week="fri", hour=17, minute=0, timezone=cron_tz),
                id="weekly_content_sprint",
                replace_existing=True,
            )
        logger.info("Sprint contenu: vendredi 17:00")
    except Exception:
        logger.exception("Sprint contenu: impossible de planifier")

    # === TELEGRAM POLLING (dev local — TELEGRAM_POLLING=1 dans .env) ===
    if settings.telegram_bot_token and settings.telegram_polling:
        import threading

        def _telegram_polling_loop() -> None:
            try:
                logger.info("Telegram polling démarré (TELEGRAM_POLLING=1)")
                get_telegram_bot().run_polling()
            except Exception:
                logger.exception("Telegram polling thread crashed")

        threading.Thread(
            target=_telegram_polling_loop,
            name="telegram-polling",
            daemon=True,
        ).start()

    yield

    try:
        from agents.bug_watchdog import stop_watchdog

        stop_watchdog()
    except Exception:
        logger.exception("BugWatchdog shutdown failed")

    if settings.telegram_bot_token:
        try:
            await get_telegram_bot().shutdown()
        except Exception:
            logger.exception("Telegram bot shutdown failed")

    if _briefing_scheduler:
        _briefing_scheduler.shutdown(wait=False)
        _briefing_scheduler = None
