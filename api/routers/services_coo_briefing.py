"""Advanced services — COO Daily Briefing (peeled from advanced_services.py)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter(prefix="/services", tags=["advanced-services"])


class BriefingRequest(BaseModel):
    context: str = ""
    include_trends: bool = True
    include_costs: bool = True
    include_events: bool = True


@router.post("/briefing/daily")
def briefing_daily(body: BriefingRequest) -> dict[str, Any]:
    """
    Briefing quotidien complet : leaderboard + trends + coûts + events → Aria synthétise.
    Déclenché chaque matin par n8n — donne les priorités du jour à Emilie.
    """
    from services.daily_briefing import run_daily_briefing
    return run_daily_briefing(
        context=body.context,
        include_trends=body.include_trends,
        include_costs=body.include_costs,
        include_events=body.include_events,
    )


@router.post("/briefing/quick")
def briefing_quick(context: str = "") -> dict[str, Any]:
    """Version rapide du briefing — leaderboard + coûts uniquement, sans trends."""
    from services.daily_briefing import run_quick_briefing
    return run_quick_briefing(context=context)
