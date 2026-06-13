"""
Brand Agent — orchestrateur CrewAI pour le pipeline Brand Kit ALNUA.

Wraps vision_llm, palette, segmentation, kit_generator — same rules as SPEC_BRANDKIT_HUB.md.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from agents.brainstorm_agent import BrainstormAgent
from database.supabase_client import get_supabase
from services.brand_schemas import BrandAnalysis
from services.brand_storage import BRAND_KITS_ROOT, ensure_brand_kit_dirs
from services.kit_generator import ALL_FORMAT_NAMES, generate_full_kit
from services.palette import extract_kmeans_colors, merge_palettes
from services.report_generator import REPORT_FILENAME, generate_brand_report
from services.segmentation import generate_isolated_assets, segment_elements
from services.vision_llm import analyze_brand_image, prepare_brand_image
from skills.skill_langfuse import trace_agent

logger = logging.getLogger(__name__)


class BrandAgent:
    """Orchestrates the full brand kit pipeline (phases 1–4)."""

    AGENT_NAME = "brand"

    def __init__(self) -> None:
        self.db = get_supabase()

    @trace_agent("brand_agent")
    def analyze_image(
        self,
        image_path: str | Path,
        project_id: str,
    ) -> dict[str, Any]:
        """Phase 1–3: LLM metadata + K-means + DINO bbox + OpenCV crop + rembg."""
        projects = self.db.select("projects", filters={"id": project_id})
        if not projects:
            raise ValueError("Project not found")
        project = projects[0]

        ensure_brand_kit_dirs()
        processed_path, _dims = prepare_brand_image(str(image_path))

        llm_analysis = analyze_brand_image(processed_path)
        kmeans_colors = extract_kmeans_colors(processed_path)
        merged_colors = merge_palettes(llm_analysis.colors, kmeans_colors)
        analysis = llm_analysis.model_copy(update={"colors": merged_colors})

        project_slug = BrainstormAgent.project_folder_slug(project["name"], project["id"])
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

        analysis_dict = analysis.model_dump()
        analysis_dict["upload_path"] = str(image_path)
        analysis_dict["segment_paths"] = segment_paths
        analysis_dict["isolated_assets"] = isolated_assets

        kit_row = self._persist_kit(project_id, project_slug, analysis_dict, [])
        return {
            "kit_id": kit_row.get("id"),
            "analysis": analysis_dict,
            "upload_path": str(image_path),
            "segment_paths": segment_paths,
            "isolated_assets": isolated_assets,
        }

    @trace_agent("brand_agent")
    def generate_kit(
        self,
        kit_id: str,
        analysis: BrandAnalysis | dict[str, Any],
    ) -> dict[str, Any]:
        """Phase 4: Pillow formats + BRAND_KIT.md + ZIP."""
        rows = self.db.select("brand_kits", filters={"id": kit_id})
        if not rows:
            raise ValueError("Brand kit not found")
        kit = rows[0]

        if isinstance(analysis, dict):
            analysis_dict = analysis
            analysis = BrandAnalysis.model_validate(analysis)
        else:
            analysis_dict = analysis.model_dump()

        project_dir = BRAND_KITS_ROOT / Path(kit["assets_path"]).name
        upload_path = analysis_dict.get("upload_path")
        if not upload_path:
            raise ValueError("upload_path missing in analysis")

        image_path = Path(upload_path)
        if not image_path.is_file():
            image_path = BRAND_KITS_ROOT.parent / str(upload_path).lstrip("/")

        generated = generate_full_kit(
            str(image_path),
            analysis,
            str(project_dir),
        )
        report_path = generate_brand_report(analysis, generated, str(project_dir))

        self.db.update(
            "brand_kits",
            kit_id,
            {
                "formats_generated": list(generated.keys()),
                "is_complete": len(generated) >= len(ALL_FORMAT_NAMES) - 1,
                "analysis": analysis.model_dump(),
            },
        )

        return {
            "kit_id": kit_id,
            "assets": generated,
            "report_path": report_path,
            "formats_generated": list(generated.keys()),
            "zip_url": f"/brand/kits/{kit_id}/download",
        }

    def _persist_kit(
        self,
        project_id: str,
        project_slug: str,
        analysis: dict[str, Any],
        formats: list[str],
    ) -> dict[str, Any]:
        assets_path = f"brand_kits/{project_slug}"
        payload = {
            "project_id": project_id,
            "brand_name": analysis.get("brand_name", "Untitled"),
            "analysis": analysis,
            "assets_path": assets_path,
            "formats_generated": formats,
            "is_complete": False,
        }
        try:
            return self.db.insert("brand_kits", payload)
        except Exception as exc:
            logger.warning("brand_kits persist skipped: %s", exc)
            return {"id": str(uuid.uuid4()), **payload}
