"""R&D routes — peeled from rnd.py (debt paydown)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()

@router.get("/rnd/dossiers/{dossier_id}/social/calendar")
def rnd_social_list_calendar(dossier_id: str) -> list[dict[str, Any]]:
    from agents.rnd_social_agent import RndSocialAgent

    try:
        return RndSocialAgent().list_calendar(dossier_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/rnd/dossiers/{dossier_id}/social/status")
def rnd_social_status(dossier_id: str) -> dict[str, Any]:
    from agents.rnd_social_agent import RndSocialAgent

    try:
        return RndSocialAgent().social_status(dossier_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/social/calendar/generate")
def rnd_social_generate_calendar(
    dossier_id: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from agents.rnd_social_agent import RndSocialAgent
    from services.rnd_schemas import RndSocialCalendarGenerateBody
    from services.rnd_social import SocialPipelineLockedError

    payload = RndSocialCalendarGenerateBody.model_validate(body or {})
    try:
        return RndSocialAgent().generate_calendar(
            dossier_id,
            force=payload.force,
            launch_date=payload.launch_date,
        )
    except SocialPipelineLockedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_social_generate_calendar failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch("/rnd/dossiers/{dossier_id}/social/calendar/{item_id}")
def rnd_social_patch_calendar(
    dossier_id: str,
    item_id: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    from agents.rnd_social_agent import RndSocialAgent
    from services.rnd_schemas import RndSocialPatchCalendarBody

    payload = RndSocialPatchCalendarBody.model_validate(body)
    try:
        return RndSocialAgent().patch_calendar_item(
            dossier_id,
            item_id,
            payload.model_dump(exclude_none=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/social/calendar/{item_id}/generate-post")
def rnd_social_generate_post(
    dossier_id: str,
    item_id: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from agents.rnd_social_agent import RndSocialAgent
    from services.rnd_schemas import RndSocialGeneratePostBody
    from services.rnd_social import SocialPipelineLockedError

    payload = RndSocialGeneratePostBody.model_validate(body or {})
    try:
        return RndSocialAgent().generate_post_for_item(
            dossier_id,
            item_id,
            platforms=payload.platforms,
        )
    except SocialPipelineLockedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_social_generate_post failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/social/generate-all")
def rnd_social_generate_all(dossier_id: str) -> dict[str, Any]:
    from agents.rnd_social_agent import RndSocialAgent
    from services.rnd_social import SocialPipelineLockedError

    try:
        return RndSocialAgent().generate_all_posts(dossier_id)
    except SocialPipelineLockedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_social_generate_all failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/rnd/dossiers/{dossier_id}/social/posts")
def rnd_social_list_posts(dossier_id: str) -> list[dict[str, Any]]:
    from agents.rnd_social_agent import RndSocialAgent

    try:
        return RndSocialAgent().list_posts(dossier_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc




