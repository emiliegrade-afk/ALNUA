"""Generate illustrated assets for R&D dossiers (phase 4) — Pillow renders."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from services.rnd_schemas import RndDossierOut
from services.rnd_visual_constants import ASSET_SPECS  # noqa: F401 — re-export
from services.rnd_visual_render import RENDERERS, palette, section_excerpt

logger = logging.getLogger(__name__)


def build_image_prompt(dossier: RndDossierOut, spec: dict[str, Any]) -> str:
    key = spec.get("section_key", "solution")
    excerpt = section_excerpt(dossier, key, 150)
    return (
        f"{spec['label']} for {dossier.title} ({dossier.domain}): {excerpt}. "
        f"Style ALNUA, dark premium, accent copper."
    )


def generate_dossier_assets(
    dossier: RndDossierOut,
    *,
    output_dir: Path,
    force: bool = False,
) -> list[dict[str, Any]]:
    """Render PNG assets to output_dir; return metadata rows for DB insert."""
    output_dir.mkdir(parents=True, exist_ok=True)
    pal = palette(dossier)
    created: list[dict[str, Any]] = []

    for spec in ASSET_SPECS:
        if spec.get("requires_finance") and not dossier.finance_json:
            continue
        path = output_dir / spec["filename"]
        if path.exists() and not force:
            created.append(_asset_row(dossier, spec, path, skipped=True))
            continue

        renderer = RENDERERS.get(spec["asset_type"])
        if not renderer:
            continue
        try:
            image = renderer(dossier, pal, spec["size"])
            image.save(path, format="PNG", optimize=True)
            created.append(_asset_row(dossier, spec, path, skipped=False))
        except Exception as exc:
            logger.warning("asset render %s failed: %s", spec["asset_type"], exc)

    return created


def _asset_row(
    dossier: RndDossierOut,
    spec: dict[str, Any],
    path: Path,
    *,
    skipped: bool,
) -> dict[str, Any]:
    w, h = spec["size"]
    rel = f"data/rnd_dossiers/{dossier.slug}/assets/{spec['filename']}"
    return {
        "dossier_id": dossier.id,
        "section_key": spec.get("section_key"),
        "asset_type": spec["asset_type"],
        "file_path": rel.replace("\\", "/"),
        "public_url": None,
        "image_prompt": build_image_prompt(dossier, spec),
        "generation_model": "pillow_v1",
        "width": w,
        "height": h,
        "metadata": {"label": spec["label"], "skipped_existing": skipped},
    }
