"""Auto-split from api/main.py — briefing routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


@router.get("/briefing/today")
def briefing_today() -> dict[str, Any]:
    db = get_supabase()
    today = date.today()
    row = get_briefing_for_date(db, today)
    if row is None:
        row = generate_and_store_daily_briefing()
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
    try:
        return generate_and_store_daily_briefing(replace_existing=True)
    except Exception as exc:
        logger.exception("briefing_generate failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/briefing/morning-run")
def briefing_morning_run(weekly_plan: bool = False) -> dict[str, Any]:
    """Briefing + plan COO + notification Telegram (sans n8n)."""
    from services.orchestration import run_morning_orchestration

    return run_morning_orchestration(weekly_plan=weekly_plan)

