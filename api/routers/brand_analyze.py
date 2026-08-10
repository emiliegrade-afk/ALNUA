"""Brand analyze route."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from api.route_common import *  # noqa: F403

router = APIRouter()

_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
_REPO_ROOT = BRAND_KITS_ROOT.parent.resolve()


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
        logger.warning("brand_kits persist skipped: %s", exc)

    return {
        "kit_id": kit_id,
        "analysis": analysis_payload,
        "upload_path": relative_upload,
        "segment_paths": segment_paths,
        "isolated_assets": isolated_assets,
    }
