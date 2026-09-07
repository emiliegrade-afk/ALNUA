"""Agent Lounge API — DEC-031 / Phase 46 V2–V6."""

from __future__ import annotations

from api.route_common import *  # noqa: F403
from services.lounge_propose import (
    contributions_transferred_count,
    list_proposals,
    propose_to_department,
)
from services.lounge_runtime import (
    complete_session,
    get_session,
    list_active_sessions,
    list_lounge_activities,
    list_lounge_challenges,
    list_puzzles,
    list_recent_sessions,
    run_session_with_llm,
    start_session,
)
from services.lounge_scores import (
    add_lounge_points,
    check_and_archive_lounge_if_new_month,
    get_lounge_leaderboard,
    get_lounge_profile,
    get_lounge_scores,
    get_lounge_team_leaderboard,
)
from services.lounge_tournaments import list_tournaments

router = APIRouter()


@router.get("/lounge/scores")
def lounge_scores(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
) -> dict[str, int]:
    check_and_archive_lounge_if_new_month()
    return get_lounge_scores(month)


@router.post("/lounge/scores")
def lounge_add_score(body: LoungeScoreAddRequest) -> dict[str, Any]:
    check_and_archive_lounge_if_new_month()
    if body.action == "custom" and body.points is None:
        raise HTTPException(status_code=400, detail="points required for custom action")
    if body.action != "custom" and body.points is not None:
        raise HTTPException(
            status_code=400,
            detail="points can only be set for custom action",
        )
    result = add_lounge_points(body.agent_id, body.action, body.points, body.note)
    logger.info(
        "lounge_score_added agent=%s action=%s points=%s",
        body.agent_id,
        body.action,
        result.get("points_added"),
    )
    return result


@router.get("/lounge/leaderboard")
def lounge_leaderboard(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
) -> list[dict[str, Any]]:
    check_and_archive_lounge_if_new_month()
    return get_lounge_leaderboard(month)


@router.get("/lounge/leaderboard/teams")
def lounge_team_leaderboard(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
) -> list[dict[str, Any]]:
    check_and_archive_lounge_if_new_month()
    return get_lounge_team_leaderboard(month)


@router.get("/lounge/profile/{agent_id}")
def lounge_profile(agent_id: str) -> dict[str, Any]:
    check_and_archive_lounge_if_new_month()
    return get_lounge_profile(agent_id)


@router.get("/lounge/activities")
def lounge_activities() -> list[dict[str, Any]]:
    return list_lounge_activities()


@router.get("/lounge/challenges")
def lounge_challenges(
    activity: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    return list_lounge_challenges(activity)


@router.get("/lounge/puzzles")
def lounge_puzzles() -> list[dict[str, Any]]:
    return list_puzzles()


@router.get("/lounge/tournaments")
def lounge_tournaments() -> list[dict[str, Any]]:
    return list_tournaments()


@router.get("/lounge/sessions/active")
def lounge_sessions_active() -> list[dict[str, Any]]:
    return list_active_sessions()


@router.get("/lounge/sessions/recent")
def lounge_sessions_recent(
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict[str, Any]]:
    return list_recent_sessions(limit)


@router.get("/lounge/sessions/{session_id}")
def lounge_session_get(session_id: str) -> dict[str, Any]:
    session = get_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")
    return session


@router.post("/lounge/sessions")
def lounge_session_start(body: LoungeSessionStartRequest) -> dict[str, Any]:
    challenge_id = body.challenge_id or body.puzzle_id
    try:
        session = start_session(body.agent_id, body.activity, challenge_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if body.run_now:
        try:
            session = run_session_with_llm(session["id"])
        except Exception as exc:
            logger.warning("lounge_llm_failed session=%s err=%s", session["id"], exc)
            return {
                **session,
                "llm_error": str(exc)[:200],
                "status": session.get("status", "active"),
            }
    return session


@router.post("/lounge/sessions/{session_id}/run")
def lounge_session_run(session_id: str) -> dict[str, Any]:
    try:
        return run_session_with_llm(session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("lounge_session_run_failed")
        raise HTTPException(status_code=502, detail=f"LLM challenge failed: {exc}") from exc


@router.post("/lounge/sessions/{session_id}/complete")
def lounge_session_complete(
    session_id: str,
    body: LoungeSessionCompleteRequest,
) -> dict[str, Any]:
    try:
        return complete_session(session_id, body.answer)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/lounge/propose")
def lounge_propose(body: LoungeProposeRequest) -> dict[str, Any]:
    try:
        result = propose_to_department(
            session_id=body.session_id,
            dept=body.dept,
            summary=body.summary,
            project_id=body.project_id,
            agent_id=body.agent_id,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info(
        "lounge_propose session=%s dept=%s ok=%s",
        body.session_id,
        body.dept,
        result.get("ok"),
    )
    return result


@router.get("/lounge/proposals")
def lounge_proposals(
    limit: int = Query(default=30, ge=1, le=100),
) -> dict[str, Any]:
    return {
        "proposals": list_proposals(limit=limit),
        "contributions_transferred": contributions_transferred_count(),
    }
