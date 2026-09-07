"""Morning briefing and secretary notification workflows."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

logger = logging.getLogger(__name__)


def run_morning_orchestration(*, weekly_plan: bool = False, notify: bool = True) -> dict[str, Any]:
    """Briefing quotidien enrichi (trends, coûts, events) + notification Telegram/Discord."""
    from services import orchestration as orch
    from services.daily_briefing import run_daily_briefing

    context = "Plan de la semaine — lundi matin." if weekly_plan else ""
    briefing_result: dict[str, Any] | None = None
    briefing_error: str | None = None
    try:
        briefing_result = run_daily_briefing(
            context=context,
            include_trends=True,
            include_costs=True,
            include_events=True,
        )
    except Exception as exc:
        briefing_error = str(exc)
        logger.exception("Morning orchestration: daily briefing failed")

    coo_brief = (briefing_result or {}).get("coo_brief") or {}
    coo_plan: str | None = None
    if coo_brief:
        coo_plan = "\n".join(
            line
            for line in (
                coo_brief.get("headline", ""),
                f"1. {coo_brief.get('priority_1', '')}",
                f"2. {coo_brief.get('priority_2', '')}",
                f"3. {coo_brief.get('priority_3', '')}",
            )
            if line and line.strip("123. ")
        ) or None

    briefing_row: dict[str, Any] | None = None
    if briefing_result:
        alerts = coo_brief.get("alerts") or []
        briefing_row = {
            "date": briefing_result.get("date"),
            "summary": coo_brief.get("headline", ""),
            "raw_data": briefing_result.get("raw_data"),
            "has_urgent": bool(alerts),
            "urgent_count": len(alerts),
            "pending_count": 0,
        }
        try:
            from services.briefing_generator import store_daily_briefing

            store_daily_briefing(orch.get_supabase(), briefing_row)
        except Exception:
            logger.debug("Morning orchestration: Supabase briefing store skipped")

    success = briefing_result is not None and coo_plan is not None
    summary = (coo_plan or briefing_error or "partial")[:200]
    orch._log_run("morning", summary, success=success)

    notifications = {"telegram": False, "discord": False}
    if coo_plan:
        alerts = coo_brief.get("alerts") or []
        alert_block = ""
        if alerts:
            alert_block = "\n\n⚠️ Alertes :\n" + "\n".join(f"• {a}" for a in alerts[:5])
        opportunities = coo_brief.get("opportunities") or []
        opp_block = ""
        if opportunities:
            opp_block = "\n\n💡 Opportunités :\n" + "\n".join(f"• {o}" for o in opportunities[:3])
        mode = "Plan de la semaine" if weekly_plan else "Briefing du jour"
        academy_line = ""
        try:
            from services.academy_progress import get_academy_status

            ac = get_academy_status().get("progress") or {}
            academy_line = (
                f"\n\n🎓 Academy : {ac.get('completed_exercises', 0)}/"
                f"{ac.get('total_exercises', 52)} exos "
                f"(L{ac.get('current_level', 1)}, "
                f"{ac.get('success_rate_pct', 0)}% succès)"
            )
        except Exception:
            pass
        message = f"☀️ ALNUA — {mode}\n\n{coo_plan}{alert_block}{opp_block}{academy_line}"
        if notify:
            notifications = orch._notify(message)

    return {
        "workflow": "morning",
        "date": date.today().isoformat(),
        "weekly_plan": weekly_plan,
        "success": success,
        "briefing": briefing_row,
        "briefing_result": briefing_result,
        "briefing_error": briefing_error,
        "coo_plan": coo_plan,
        "coo_error": briefing_error if not coo_plan else None,
        "notifications": notifications,
    }


def run_secretary_morning_notify(*, weekly_plan: bool = False) -> dict[str, Any]:
    """
    8h Paris — briefing LLM une seule fois, puis message Nadia (Telegram dédié).
    """
    from services import orchestration as orch_mod
    from services.secretary_intents import build_combined_morning_message
    from skills.skill_telegram_notify import notify_telegram_secretary

    morning_result = run_morning_orchestration(weekly_plan=weekly_plan, notify=False)
    cached = morning_result.get("briefing_result")
    if isinstance(cached, dict):
        message = build_combined_morning_message(briefing_result=cached)
    else:
        message = build_combined_morning_message()
    telegram_ok = False
    try:
        from services.notify_dedup import should_send_notify

        if should_send_notify("telegram_secretary", message):
            telegram_ok = notify_telegram_secretary(message)
    except Exception:
        telegram_ok = notify_telegram_secretary(message)
    voice_ok = False
    if telegram_ok:
        try:
            from services.telegram_voice import send_overlay_voice_http

            voice_ok = send_overlay_voice_http(message)
        except Exception:
            logger.warning("secretary morning voice overlay skipped", exc_info=True)
    orch_mod._log_run(
        "secretary_morning",
        (morning_result.get("coo_plan") or "partial")[:120],
        success=bool(morning_result.get("success")),
    )
    return {
        "workflow": "secretary_morning",
        "orchestration": morning_result,
        "notifications": {"telegram": telegram_ok, "telegram_voice": voice_ok},
        "message_preview": message[:300],
    }
