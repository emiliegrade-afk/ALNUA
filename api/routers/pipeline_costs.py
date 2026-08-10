"""Pipeline cost summary routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


@router.get("/costs/today")
async def costs_today():
    try:
        return get_daily_costs()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/costs/month")
async def costs_month():
    try:
        return get_monthly_costs()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/costs/week")
async def costs_week():
    try:
        return get_weekly_costs()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
