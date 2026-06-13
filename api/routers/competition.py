"""Auto-split from api/main.py — competition routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


@router.get("/agents/scores")
def competition_scores(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
) -> dict[str, int]:
    check_and_archive_if_new_month()
    return get_scores(month)


@router.post("/agents/scores")
def competition_add_score(body: ScoreAddRequest) -> dict[str, Any]:
    check_and_archive_if_new_month()
    if body.action == "custom" and body.points is None:
        raise HTTPException(status_code=400, detail="points required for custom action")
    if body.action != "custom" and body.points is not None:
        raise HTTPException(
            status_code=400,
            detail="points can only be set for custom action",
        )
    result = add_points(body.agent_id, body.action, body.points, body.note)
    logger.info(
        "agent_score_added agent=%s action=%s points=%s note=%s",
        body.agent_id,
        body.action,
        result.get("points_added"),
        body.note[:80] if body.note else "",
    )
    return result


@router.get("/agents/leaderboard")
def competition_leaderboard(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
) -> list[dict[str, Any]]:
    check_and_archive_if_new_month()
    return get_leaderboard(month)


@router.get("/agents/leaderboard/teams")
def competition_team_leaderboard(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
) -> list[dict[str, Any]]:
    check_and_archive_if_new_month()
    return get_team_leaderboard(month)


