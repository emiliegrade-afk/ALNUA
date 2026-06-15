"""Auto-split from api/main.py — briefing routes (canonical operational briefing API)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from services.facades.briefing_facade import (
    fetch_operational_briefing_for_date,
    is_briefing_unified_generate_enabled,
)

router = APIRouter()


@router.get("/briefing/today")
def briefing_today(ensure: bool = Query(default=False)) -> dict[str, Any]:
    """Return today's briefing. LLM generation only when ensure=true (POST /generate preferred)."""
    db = get_supabase()
    today = date.today()
    row = fetch_operational_briefing_for_date(db, today)
    if row is None:
        if ensure:
            row = generate_and_store_daily_briefing()
        else:
            raise HTTPException(status_code=404, detail="No briefing for today")
    return row


@router.get("/briefing/history")
def briefing_history(limit: int = Query(default=30, ge=1, le=100)) -> list[dict[str, Any]]:
    db = get_supabase()
    response = (
        db.table("daily_briefings")
        .select("*")
        .order("date", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


@router.post("/briefing/generate")
def briefing_generate() -> dict[str, Any]:
    """Operational briefing; when unified flag is on, also runs morning orchestration."""
    try:
        row = generate_and_store_daily_briefing(replace_existing=True)
        if is_briefing_unified_generate_enabled():
            from services.orchestration import run_morning_orchestration

            orch = run_morning_orchestration()
            return {**row, "unified": True, "orchestration": orch}
        return row
    except Exception as exc:
        logger.exception("briefing_generate failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post(
    "/briefing/morning-run",
    deprecated=True,
    description="Prefer POST /orchestration/morning (same pipeline, n8n-friendly prefix).",
)
def briefing_morning_run(weekly_plan: bool = False) -> dict[str, Any]:
    """Briefing + plan COO + notification Telegram (sans n8n)."""
    from services.orchestration import run_morning_orchestration

    return run_morning_orchestration(weekly_plan=weekly_plan)
