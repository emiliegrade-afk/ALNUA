"""R&D routes — peeled from rnd.py (debt paydown)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()

@router.get("/rnd/product/{slug}")
def rnd_public_product_page(slug: str) -> dict[str, Any]:
    """Fiche produit publique (published=true uniquement)."""
    from agents.rnd_product_agent import RndProductAgent

    try:
        return RndProductAgent().get_public_page(slug)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/rnd/dossiers/{dossier_id}/product")
def rnd_get_product_page(dossier_id: str) -> dict[str, Any]:
    from agents.rnd_product_agent import RndProductAgent

    try:
        return RndProductAgent().get_product_page(dossier_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/rnd/dossiers/{dossier_id}/product/status")
def rnd_product_status(dossier_id: str) -> dict[str, Any]:
    from agents.rnd_product_agent import RndProductAgent

    try:
        return RndProductAgent().product_status(dossier_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/product/generate")
def rnd_generate_product_page(
    dossier_id: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from agents.rnd_product_agent import RndProductAgent
    from services.rnd_product import ProductPipelineLockedError
    from services.rnd_schemas import RndProductGenerateBody

    payload = RndProductGenerateBody.model_validate(body or {})
    try:
        return RndProductAgent().generate_product_page(
            dossier_id,
            force=payload.force,
            waitlist_enabled=payload.waitlist_enabled,
        )
    except ProductPipelineLockedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_generate_product_page failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch("/rnd/dossiers/{dossier_id}/product")
def rnd_patch_product_page(dossier_id: str, body: dict[str, Any]) -> dict[str, Any]:
    from agents.rnd_product_agent import RndProductAgent
    from services.rnd_schemas import RndProductPatchBody

    payload = RndProductPatchBody.model_validate(body)
    values = payload.model_dump(exclude_none=True)
    try:
        return RndProductAgent().update_product_page(dossier_id, values=values)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/product/publish")
def rnd_publish_product_page(dossier_id: str) -> dict[str, Any]:
    from agents.rnd_product_agent import RndProductAgent
    from services.rnd_product import ProductPipelineLockedError

    try:
        return RndProductAgent().publish_product_page(dossier_id)
    except ProductPipelineLockedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_publish_product_page failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/product/unpublish")
def rnd_unpublish_product_page(dossier_id: str) -> dict[str, Any]:
    from agents.rnd_product_agent import RndProductAgent

    try:
        return RndProductAgent().unpublish_product_page(dossier_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


# Finance summary/dashboard: canonical handlers in api/routers/finances.py (Phase 4).
# Paths unchanged — implementation moved out of this god router.
