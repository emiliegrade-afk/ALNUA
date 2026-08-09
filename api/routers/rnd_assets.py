"""R&D routes — peeled from rnd.py (debt paydown)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()

@router.get("/rnd/dossiers/{dossier_id}/assets")
def rnd_list_dossier_assets(dossier_id: str) -> list[dict[str, Any]]:
    from agents.rnd_visual_agent import RndVisualAgent

    try:
        assets = RndVisualAgent().list_assets(dossier_id)
        return [a.model_dump() for a in assets]
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/assets/generate")
def rnd_generate_dossier_assets(
    dossier_id: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from agents.rnd_visual_agent import RndVisualAgent
    from services.rnd_schemas import RndAssetsGenerateBody

    payload = RndAssetsGenerateBody.model_validate(body or {})
    try:
        result = RndVisualAgent().generate_assets(dossier_id, force=payload.force)
        result["assets"] = [
            {
                **a,
                "file_url": f"/rnd/dossiers/{dossier_id}/assets/file?asset_type={a['asset_type']}",
            }
            for a in result.get("assets", [])
        ]
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_generate_dossier_assets failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/rnd/dossiers/{dossier_id}/assets/file")
def rnd_dossier_asset_file(
    dossier_id: str,
    request: Request,
    asset_type: str | None = Query(default=None),
    asset_id: str | None = Query(default=None),
) -> FileResponse:
    from services.rnd_product import RndProductRepository
    from services.rnd_repository import get_rnd_repository

    if not asset_type and not asset_id:
        raise HTTPException(status_code=400, detail="asset_type ou asset_id requis")

    if not hub_api_key_valid(request.headers.get("X-Hub-Key")):
        page = RndProductRepository().get_by_dossier_id(dossier_id)
        if not page or not page.published:
            raise HTTPException(status_code=403, detail="Asset non public")

    dossier = get_rnd_repository().get_dossier(dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    assets = get_rnd_repository().list_assets(dossier.id)
    match = None
    if asset_id:
        match = next((a for a in assets if str(a.id) == str(asset_id)), None)
    elif asset_type:
        match = next((a for a in assets if a.asset_type == asset_type), None)
    if not match:
        raise HTTPException(status_code=404, detail="Asset introuvable")

    repo_root = get_hub_repo_path()
    data_root = RND_DOSSIERS_DATA_ROOT.resolve()

    path = Path(match.file_path)
    if not path.is_absolute():
        path = (repo_root / match.file_path.replace("\\", "/").lstrip("/")).resolve()
    else:
        path = path.resolve()

    if not str(path).startswith(str(data_root)):
        raise HTTPException(status_code=403, detail="Accès refusé")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Fichier asset introuvable")

    return FileResponse(path, media_type="image/png", filename=path.name)


@router.post("/rnd/dossiers/{dossier_id}/deck/generate")
def rnd_generate_deck(dossier_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    from services.rnd_deck import generate_dossier_deck

    export_pdf = True
    if body and "export_pdf" in body:
        export_pdf = bool(body["export_pdf"])
    try:
        result = generate_dossier_deck(dossier_id, export_pdf=export_pdf)
        dossier_id_resolved = result["dossier_id"]
        result["html_url"] = f"/rnd/dossiers/{dossier_id_resolved}/deck/file?type=html"
        if result.get("pdf_path"):
            result["pdf_url"] = f"/rnd/dossiers/{dossier_id_resolved}/deck/file?type=pdf"
        else:
            result["pdf_url"] = None
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_generate_deck failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/rnd/dossiers/{dossier_id}/deck/file")
def rnd_deck_file(
    dossier_id: str,
    type: str = Query(..., pattern="^(html|pdf)$"),
) -> FileResponse:
    from services.rnd_repository import get_rnd_repository

    dossier = get_rnd_repository().get_dossier(dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    stored = dossier.deck_pdf_path if type == "pdf" else dossier.deck_html_path
    if not stored:
        raise HTTPException(status_code=404, detail="Deck non généré")

    repo_root = get_hub_repo_path()
    data_root = RND_DOSSIERS_DATA_ROOT.resolve()

    path = Path(stored)
    if not path.is_absolute():
        path = (repo_root / stored.replace("\\", "/").lstrip("/")).resolve()
    else:
        path = path.resolve()

    if not str(path).startswith(str(data_root)):
        raise HTTPException(status_code=403, detail="Accès refusé")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Fichier deck introuvable")

    media = "application/pdf" if type == "pdf" else "text/html"
    return FileResponse(path, media_type=media, filename=path.name)




