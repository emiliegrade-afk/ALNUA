"""R&D routes — peeled from rnd.py (debt paydown)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()

@router.post("/rnd/dossiers/{dossier_id}/committee/start")
def rnd_committee_start(dossier_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    from agents.rnd_committee_agent import RndCommitteeAgent
    from services.rnd_schemas import RndCommitteeStartBody

    payload = RndCommitteeStartBody.model_validate(body or {})
    try:
        return RndCommitteeAgent().start_session(
            dossier_id,
            mode=payload.mode,
            active_section=payload.active_section,
            force_new=payload.force_new,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_committee_start failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/rnd/dossiers/{dossier_id}/committee/sessions")
def rnd_committee_list_sessions(dossier_id: str) -> list[dict[str, Any]]:
    from agents.rnd_committee_agent import RndCommitteeAgent

    return RndCommitteeAgent().list_sessions(dossier_id)


@router.get("/rnd/dossiers/{dossier_id}/committee/{session_id}")
def rnd_committee_get_session(dossier_id: str, session_id: str) -> dict[str, Any]:
    from agents.rnd_committee_agent import RndCommitteeAgent

    try:
        return RndCommitteeAgent().get_session_with_messages(dossier_id, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/committee/{session_id}/message")
def rnd_committee_message(
    dossier_id: str,
    session_id: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    from agents.rnd_committee_agent import RndCommitteeAgent
    from services.rnd_schemas import RndCommitteeMessageBody

    payload = RndCommitteeMessageBody.model_validate(body)
    try:
        return RndCommitteeAgent().post_message(
            dossier_id,
            session_id,
            payload.message,
            target_speaker=payload.target_speaker,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_committee_message failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/committee/{session_id}/report")
def rnd_committee_generate_report(
    dossier_id: str,
    session_id: str,
) -> dict[str, Any]:
    """Génère le CR structuré sans clôturer la session comité."""
    from agents.rnd_committee_agent import RndCommitteeAgent

    try:
        return RndCommitteeAgent().generate_session_report(dossier_id, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_committee_generate_report failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/committee/{session_id}/close")
def rnd_committee_close(
    dossier_id: str,
    session_id: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from agents.rnd_committee_agent import RndCommitteeAgent
    from services.rnd_schemas import RndCommitteeCloseBody

    payload = RndCommitteeCloseBody.model_validate(body or {})
    try:
        return RndCommitteeAgent().close_session(
            dossier_id,
            session_id,
            apply_sections=payload.apply_sections,
            generate_ceo_package=payload.generate_ceo_package,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_committee_close failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc



RND_DOSSIERS_DATA_ROOT = data_dir("rnd_dossiers")


