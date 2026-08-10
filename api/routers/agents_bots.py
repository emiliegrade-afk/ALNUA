"""Reviews and publisher/analytics bot cycle routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


@router.post("/reviews/sync")
def reviews_sync(body: ReviewsSyncRequest) -> dict[str, Any]:
    bot = ReviewsBot()
    if body.project_id:
        ingested = bot.sync_project(body.project_id)
        return {"ingested": ingested}
    return bot.run_cycle()


@router.post("/bots/publisher/run")
def publisher_run_cycle() -> dict[str, Any]:
    return PublisherBot().run_cycle()


@router.post("/bots/analytics/run")
def analytics_run_cycle() -> dict[str, Any]:
    result = AnalyticsBot().run_cycle()
    return {"metrics_recorded": result.get("recorded", 0), **result}
