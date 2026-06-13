"""Auto-split from api/main.py — brand routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
_REPO_ROOT = BRAND_KITS_ROOT.parent.resolve()
_FULL_KIT_FORMAT_COUNT = len(ALL_FORMAT_NAMES)


class BrandGenerateKitRequest(BaseModel):
    kit_id: str | None = None
    project_id: str
    formats: list[str] | None = None
    upload_path: str | None = None
    analysis: dict[str, Any] | None = None


class BrandOpenFolderRequest(BaseModel):
    kit_id: str


class BrandRefineSegmentsRequest(BaseModel):
    elements: list[BrandElement]
    labels: list[str] | None = None
    force_bbox: bool = Field(
        default=True,
        description="When true, skip OpenCV panel snap and use bbox as-is.",
    )


def _resolve_repo_path(relative_path: str) -> Path:
    normalized = relative_path.replace("\\", "/").lstrip("/")
    if ".." in normalized.split("/"):
        raise HTTPException(status_code=400, detail="Chemin invalide")
    file_path = (_REPO_ROOT / normalized).resolve()
    if not str(file_path).startswith(str(_REPO_ROOT)):
        raise HTTPException(status_code=400, detail="Chemin invalide")
    return file_path


def _kit_project_dir(assets_path: str) -> Path:
    return _resolve_repo_path(assets_path)


def _create_kit_zip(assets: dict[str, str], report_path: str | None) -> io.BytesIO:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for format_name, rel_path in sorted(assets.items()):
            full_path = _resolve_repo_path(rel_path)
            if full_path.is_file():
                suffix = full_path.suffix or ".png"
                archive.write(full_path, arcname=f"{format_name}{suffix}")
        if report_path:
            report_full = _resolve_repo_path(report_path)
            if report_full.is_file():
                archive.write(report_full, arcname=REPORT_FILENAME)
    buffer.seek(0)
    return buffer


def _load_brand_kit(kit_id: str) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("brand_kits", filters={"id": kit_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Kit introuvable")
    return rows[0]


@router.post("/brand/analyze")
async def brand_analyze(
    file: UploadFile = File(...),
    project_id: str = Form(...),
) -> dict[str, Any]:
    """Upload brand image, run GPT-4V metadata + Grounding DINO bboxes + K-means."""
    db = get_supabase()
    projects = db.select("projects", filters={"id": project_id})
    if not projects:
        raise HTTPException(status_code=404, detail="Projet introuvable")

    project = projects[0]

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Le fichier doit être une image")

    ensure_brand_kit_dirs()

    ext = Path(file.filename or "").suffix.lower()
    if ext not in _IMAGE_EXTENSIONS:
        ext = ".png" if file.content_type == "image/png" else ".jpg"

    upload_path = BRAND_KITS_ROOT / "uploads" / f"{uuid.uuid4()}{ext}"
    upload_path.write_bytes(await file.read())

    # Same resized image for DINO bbox + OpenCV crop (spec pipeline rule).
    processed_path, (img_w, img_h) = prepare_brand_image(str(upload_path))

    llm_analysis = analyze_brand_image(processed_path)
    kmeans_colors = extract_kmeans_colors(processed_path)
    merged_colors = merge_palettes(llm_analysis.colors, kmeans_colors)

    analysis = llm_analysis.model_copy(update={"colors": merged_colors})

    project_slug = BrainstormAgent.project_folder_slug(project["name"], project["id"])
    assets_path = f"brand_kits/{project_slug}"
    project_dir = BRAND_KITS_ROOT / project_slug
    segments_dir = project_dir / "segments"
    isolated_dir = project_dir / "isolated"

    segment_paths = segment_elements(
        processed_path,
        analysis.elements,
        segments_dir=str(segments_dir),
    )
    isolated_assets = generate_isolated_assets(
        processed_path,
        analysis,
        str(isolated_dir),
    )

    relative_upload = str(Path(processed_path).relative_to(_REPO_ROOT)).replace("\\", "/")
    analysis_payload = analysis.model_dump(mode="json")
    analysis_payload["segment_paths"] = segment_paths
    analysis_payload["isolated_assets"] = isolated_assets
    analysis_payload["upload_path"] = relative_upload
    analysis_payload["source_size"] = {"width": img_w, "height": img_h}

    kit_id: str | None = None
    try:
        kit_row = db.insert(
            "brand_kits",
            {
                "project_id": project_id,
                "brand_name": analysis.brand_name,
                "analysis": analysis_payload,
                "assets_path": assets_path,
                "formats_generated": [],
            },
        )
        kit_id = kit_row["id"]
    except Exception as exc:
        # Table may not exist yet — analysis still usable in UI
        logger.warning("brand_kits persist skipped: %s", exc)

    return {
        "kit_id": kit_id,
        "analysis": analysis_payload,
        "upload_path": relative_upload,
        "segment_paths": segment_paths,
        "isolated_assets": isolated_assets,
    }


@router.post("/brand/generate-kit")
def brand_generate_kit(body: BrandGenerateKitRequest) -> dict[str, Any]:
    """Generate all kit formats, write BRAND_KIT.md, update Supabase."""
    db = get_supabase()
    kit: dict[str, Any] | None = None
    analysis_raw: dict[str, Any]
    assets_path: str
    kit_id: str

    if body.kit_id:
        kit = _load_brand_kit(body.kit_id)
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

    image_path = _resolve_repo_path(upload_path)
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image source introuvable")

    brand_data = BrandAnalysis.model_validate(analysis_raw)
    project_dir = _kit_project_dir(assets_path)

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
    kit = _load_brand_kit(kit_id)
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
    kit = _load_brand_kit(kit_id)
    analysis = kit["analysis"]
    assets: dict[str, str] = analysis.get("generated_assets") or analysis.get("isolated_assets") or {}
    if not assets:
        raise HTTPException(status_code=404, detail="Aucun asset généré pour ce kit")

    report_path = analysis.get("report_path")
    buffer = _create_kit_zip(assets, report_path)
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
    kit = _load_brand_kit(kit_id)
    analysis_raw: dict[str, Any] = dict(kit["analysis"])
    upload_path = analysis_raw.get("upload_path")
    if not upload_path:
        raise HTTPException(status_code=400, detail="upload_path manquant dans l'analyse")

    image_path = _resolve_repo_path(upload_path)
    if not image_path.is_file():
        raise HTTPException(status_code=404, detail="Image source introuvable")

    use_panel_snap = not body.force_bbox
    labels_filter = set(body.labels) if body.labels else None

    brand_data = BrandAnalysis.model_validate(
        {**analysis_raw, "elements": [el.model_dump() for el in body.elements]}
    )
    project_dir = _kit_project_dir(kit["assets_path"])
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
    kit = _load_brand_kit(body.kit_id)
    folder = _kit_project_dir(kit["assets_path"])
    if not folder.is_dir():
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    subprocess.Popen(["explorer", str(folder)])
    return {"ok": True}


@router.get("/brand/assets")
async def brand_asset(path: str = Query(..., min_length=1)) -> FileResponse:
    """Serve a brand kit file by repo-relative path (e.g. brand_kits/slug/isolated/symbol_transparent.png)."""
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


