"""Brand kit shared helpers and request models."""

from __future__ import annotations

import io
import zipfile
from pathlib import Path
from typing import Any

from api.route_common import *  # noqa: F403

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


def resolve_repo_path(relative_path: str) -> Path:
    normalized = relative_path.replace("\\", "/").lstrip("/")
    if ".." in normalized.split("/"):
        raise HTTPException(status_code=400, detail="Chemin invalide")
    file_path = (_REPO_ROOT / normalized).resolve()
    if not str(file_path).startswith(str(_REPO_ROOT)):
        raise HTTPException(status_code=400, detail="Chemin invalide")
    return file_path


def kit_project_dir(assets_path: str) -> Path:
    return resolve_repo_path(assets_path)


def create_kit_zip(assets: dict[str, str], report_path: str | None) -> io.BytesIO:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for format_name, rel_path in sorted(assets.items()):
            full_path = resolve_repo_path(rel_path)
            if full_path.is_file():
                suffix = full_path.suffix or ".png"
                archive.write(full_path, arcname=f"{format_name}{suffix}")
        if report_path:
            report_full = resolve_repo_path(report_path)
            if report_full.is_file():
                archive.write(report_full, arcname=REPORT_FILENAME)
    buffer.seek(0)
    return buffer


def load_brand_kit(kit_id: str) -> dict[str, Any]:
    db = get_supabase()
    rows = db.select("brand_kits", filters={"id": kit_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Kit introuvable")
    return rows[0]
