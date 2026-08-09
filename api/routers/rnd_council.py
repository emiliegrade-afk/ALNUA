"""Moteur Conseil R&D — Conseil stratégique + Conseil IA (Phase 25, ROADMAP.md)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


@router.post("/rnd/council/sessions")
def rnd_council_start_session(body: dict[str, Any]) -> dict[str, Any]:
    """Démarre une session Conseil stratégique (débat libre, sans dossier)."""
    from agents.rnd_council_agent import RndCouncilAgent
    from services.rnd_schemas import RndCouncilStartBody

    payload = RndCouncilStartBody.model_validate(body)
    try:
        return RndCouncilAgent().start_session(
            kind=payload.kind, topic=payload.topic, idea_id=payload.idea_id
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/rnd/council/sessions/{session_id}")
def rnd_council_get_session(session_id: str) -> dict[str, Any]:
    from agents.rnd_council_agent import RndCouncilAgent

    agent = RndCouncilAgent()
    session = agent.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session Conseil introuvable")
    return {"session": session, "messages": agent.list_messages(session_id)}


@router.post("/rnd/council/sessions/{session_id}/message")
async def rnd_council_post_message(session_id: str, body: dict[str, Any]) -> dict[str, Any]:
    from agents.rnd_council_agent import RndCouncilAgent
    from services.rnd_schemas import RndCouncilMessageBody

    payload = RndCouncilMessageBody.model_validate(body)
    try:
        return await RndCouncilAgent().post_message(session_id, payload.message, actor="emilie")
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/rnd/council/sessions/{session_id}/gauges")
def rnd_council_gauges(session_id: str) -> dict[str, Any]:
    from agents.rnd_council_agent import RndCouncilAgent

    return RndCouncilAgent().compute_gauges(session_id)


@router.post("/rnd/council/sessions/{session_id}/close")
def rnd_council_close_session(session_id: str) -> dict[str, Any]:
    from agents.rnd_council_agent import RndCouncilAgent

    try:
        return RndCouncilAgent().close_session(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/council/evaluate")
async def rnd_council_evaluate(body: dict[str, Any]) -> dict[str, Any]:
    """Conseil IA — un seul appel : input structuré → débat → Décision Collective."""
    from agents.rnd_council_agent import RndCouncilAgent
    from services.rnd_schemas import RndCouncilEvaluateBody

    payload = RndCouncilEvaluateBody.model_validate(body)
    try:
        return await RndCouncilAgent().evaluate(
            topic=payload.topic,
            structured_input=payload.structured_input.model_dump(),
            idea_id=payload.idea_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
