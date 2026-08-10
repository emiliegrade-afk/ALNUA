"""Brand kit CRUD and asset routes."""

from __future__ import annotations

from typing import Any

from api.route_common import *  # noqa: F403
from api.routers.brand_helpers import (
    BrandGenerateKitRequest,
    BrandOpenFolderRequest,
    BrandRefineSegmentsRequest,
    _FULL_KIT_FORMAT_COUNT,
    create_kit_zip,
    kit_project_dir,
    load_brand_kit,
    resolve_repo_path,
)

router = APIRouter()


@router.post("/brand/generate-kit")
def brand_generate_kit(body: BrandGenerateKitRequest) -> dict[str, Any]:
    """Generate all kit formats, write BRAND_KIT.md, update Supabase."""
    db = get_supabase()
    kit: dict[str, Any] | None = None
    analysis_raw: dict[str, Any]
    assets_path: str
    kit_id: str

    if body.kit_id:
        kit = load_brand_kit(body.kit_id)
        if kit["project_id"] != body.project_id:
            raise HTTPException(status_code=400, detail="project_id ne correspond pas au kit")
        analysis_raw = kit["analysis"]
        assets_path = kit["assets_path"]
        kit_id = body.kit_id
    else:
        if not body.upload_path or not body.analysis:
            raise HTTPException(
                status_code=400,
                detail="kit_id ou (upload_path + analysis) requis",
            )
        projects = db.select("projects", filters={"id": body.project_id})
        if not projects:
            raise HTTPException(status_code=404, detail="Projet introuvable")
        project = projects[0]
        project_slug = BrainstormAgent.project_folder_slug(project["name"], project["id"])
        assets_path = f"brand_kits/{project_slug}"
        analysis_raw = {**body.analysis, "upload_path": body.upload_path}

        brand_name = analysis_raw.get("brand_name") or "Brand"
        try:
            kit_row = db.insert(
                "brand_kits",
                {
                    "project_id": body.project_id,
                    "brand_name": brand_name,
                    "analysis": analysis_raw,
                    "assets_path": assets_path,
                    "formats_generated": [],
                },
            )
            kit_id = kit_row["id"]
        except Exception as exc:
            logger.warning("brand_kits insert on generate skipped: %s", exc)
            kit_id = str(uuid.uuid4())

    upload_path = analysis_raw.get("upload_path")
    if not upload_path:
        raise HTTPException(status_code=400, detail="upload_path manquant dans l'analyse")

    image_path = resolve_repo_path(upload_path)
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image source introuvable")

    brand_data = BrandAnalysis.model_validate(analysis_raw)
    project_dir = kit_project_dir(assets_path)

    generated = generate_full_kit(
        str(image_path),
        brand_data,
        str(project_dir),
        formats=body.formats,
    )

    report_path = generate_brand_report(brand_data, generated, str(project_dir))
    formats_generated = sorted(set(generated.keys()))
    updated_analysis = {
        **analysis_raw,
        "generated_assets": generated,
        "report_path": report_path,
    }

    try:
        if kit is not None or body.kit_id:
            db.update(
                "brand_kits",
                kit_id,
                {
                    "formats_generated": formats_generated,
                    "analysis": updated_analysis,
                },
            )
        elif body.upload_path and body.analysis:
            db.update(
                "brand_kits",
                kit_id,
                {
                    "formats_generated": formats_generated,
                    "analysis": updated_analysis,
                },
            )
    except Exception as exc:
        logger.warning("brand_kits update skipped: %s", exc)

    return {
        "kit_id": kit_id,
        "assets": generated,
        "report_path": report_path,
        "zip_url": f"/brand/kits/{kit_id}/download",
        "formats_generated": formats_generated,
    }


@router.get("/brand/kits")
def brand_list_kits(
    project_id: str | None = Query(default=None),
) -> list[dict[str, Any]]:
    """List brand kits, optionally filtered by project."""
    db = get_supabase()
    filters = {"project_id": project_id} if project_id else None
    rows = db.select(
        "brand_kits",
        filters=filters,
        order_by="created_at",
        ascending=False,
    )
    return [
        {
            "id": row["id"],
            "project_id": row["project_id"],
            "brand_name": row["brand_name"],
            "assets_path": row["assets_path"],
            "formats_generated": row.get("formats_generated") or [],
            "is_complete": len(row.get("formats_generated") or []) >= _FULL_KIT_FORMAT_COUNT,
            "created_at": row.get("created_at"),
            "updated_at": row.get("updated_at"),
        }
        for row in rows
    ]


@router.get("/brand/kits/{kit_id}")
def brand_get_kit(kit_id: str) -> dict[str, Any]:
    """Return full kit record including analysis."""
    kit = load_brand_kit(kit_id)
    analysis = kit["analysis"]
    generated_assets = analysis.get("generated_assets") or analysis.get("isolated_assets") or {}
    return {
        "id": kit["id"],
        "project_id": kit["project_id"],
        "brand_name": kit["brand_name"],
        "analysis": analysis,
        "assets_path": kit["assets_path"],
        "formats_generated": kit.get("formats_generated") or [],
        "generated_assets": generated_assets,
        "report_path": analysis.get("report_path"),
        "upload_path": analysis.get("upload_path"),
        "segment_paths": analysis.get("segment_paths") or {},
        "isolated_assets": analysis.get("isolated_assets") or {},
        "is_complete": len(kit.get("formats_generated") or []) >= _FULL_KIT_FORMAT_COUNT,
        "created_at": kit.get("created_at"),
        "updated_at": kit.get("updated_at"),
    }


@router.get("/brand/kits/{kit_id}/download")
def brand_download_kit(kit_id: str) -> StreamingResponse:
    """Stream a ZIP archive of all generated kit assets."""
    kit = load_brand_kit(kit_id)
    analysis = kit["analysis"]
    assets: dict[str, str] = analysis.get("generated_assets") or analysis.get("isolated_assets") or {}
    if not assets:
        raise HTTPException(status_code=404, detail="Aucun asset généré pour ce kit")

    report_path = analysis.get("report_path")
    buffer = create_kit_zip(assets, report_path)
    brand_slug = kit["brand_name"].replace(" ", "_").lower()
    filename = f"brand_kit_{brand_slug}.zip"

    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/brand/kits/{kit_id}/refine-segments")
def brand_refine_segments(
    kit_id: str,
    body: BrandRefineSegmentsRequest,
) -> dict[str, Any]:
    """Re-crop segments after manual bbox adjustment — no LLM re-run."""
    kit = load_brand_kit(kit_id)
    analysis_raw: dict[str, Any] = dict(kit["analysis"])
    upload_path = analysis_raw.get("upload_path")
    if not upload_path:
        raise HTTPException(status_code=400, detail="upload_path manquant dans l'analyse")

    image_path = resolve_repo_path(upload_path)
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image source introuvable")

    use_panel_snap = not body.force_bbox
    labels_filter = set(body.labels) if body.labels else None

    brand_data = BrandAnalysis.model_validate(
        {**analysis_raw, "elements": [el.model_dump() for el in body.elements]}
    )
    project_dir = kit_project_dir(kit["assets_path"])
    segments_dir = project_dir / "segments"
    isolated_dir = project_dir / "isolated"

    segment_paths = segment_elements(
        str(image_path),
        brand_data.elements,
        segments_dir=str(segments_dir),
        use_panel_snap=use_panel_snap,
        labels_filter=labels_filter,
        existing_paths=analysis_raw.get("segment_paths") or {},
    )
    isolated_assets = generate_isolated_assets(
        str(image_path),
        brand_data,
        str(isolated_dir),
        use_panel_snap=use_panel_snap,
    )

    updated_analysis = {
        **analysis_raw,
        "elements": [el.model_dump() for el in body.elements],
        "segment_paths": segment_paths,
        "isolated_assets": isolated_assets,
    }

    db = get_supabase()
    try:
        db.update(
            "brand_kits",
            kit_id,
            {"analysis": updated_analysis, "brand_name": brand_data.brand_name},
        )
    except Exception as exc:
        logger.warning("brand_kits refine update skipped: %s", exc)

    return {
        "kit_id": kit_id,
        "analysis": updated_analysis,
        "segment_paths": segment_paths,
        "isolated_assets": isolated_assets,
    }


@router.post("/brand/open-folder")
def brand_open_folder(body: BrandOpenFolderRequest) -> dict[str, bool]:
    """Open the kit folder in Windows Explorer."""
    kit = load_brand_kit(body.kit_id)
    folder = kit_project_dir(kit["assets_path"])
    if not folder.is_dir():
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    subprocess.Popen(["explorer", str(folder)])
    return {"ok": True}


@router.get("/brand/assets")
async def brand_asset(path: str = Query(..., min_length=1)) -> FileResponse:
    """Serve a brand kit file by repo-relative path."""
    normalized = path.replace("\\", "/").lstrip("/")
    if ".." in normalized.split("/"):
        raise HTTPException(status_code=400, detail="Chemin invalide")

    brand_root = BRAND_KITS_ROOT.resolve()
    repo_root = brand_root.parent
    file_path = (repo_root / normalized).resolve()

    if not str(file_path).startswith(str(brand_root)):
        raise HTTPException(status_code=403, detail="Acces refuse")
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Asset introuvable")

    return FileResponse(file_path)
