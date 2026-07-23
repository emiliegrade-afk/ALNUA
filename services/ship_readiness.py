"""Branch-specific release readiness — gaming (GDD/Godot) & robotics (BOM/hardware)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger(__name__)

BranchKind = Literal["gaming", "robotics"]


def _project_root(local_path: str) -> Path | None:
    p = Path(local_path).expanduser()
    if not p.exists():
        return None
    return p


def _find_markdown(root: Path, patterns: list[str], min_chars: int = 80) -> tuple[bool, str, list[str]]:
    """Search pole/slug layouts and repo root for deliverable markdown."""
    gaps: list[str] = []
    for pattern in patterns:
        for hit in root.glob(pattern):
            if hit.is_file():
                try:
                    text = hit.read_text(encoding="utf-8", errors="ignore").strip()
                except Exception:
                    continue
                if len(text) >= min_chars:
                    return True, str(hit.relative_to(root)), gaps
                gaps.append(f"{hit.name}.too_short")
    return False, "", gaps or [f"missing:{patterns[0]}"]


def check_gaming_readiness(
    local_path: str,
    *,
    slug: str = "",
    min_gdd_chars: int = 120,
) -> dict[str, Any]:
    """Godot project + GDD extract or equivalent design doc."""
    root = _project_root(local_path)
    if not root:
        return {
            "ready": False,
            "detail": f"Chemin introuvable : {local_path}",
            "gaps": ["local_path.missing"],
        }

    gaps: list[str] = []
    godot_files = list(root.rglob("project.godot"))
    if not godot_files:
        gaps.append("godot.project_missing")

    gdd_patterns = [
        f"gaming/{slug}/gdd-extract.md" if slug else "gaming/*/gdd-extract.md",
        "gaming/**/gdd*.md",
        "docs/gdd*.md",
        "GDD.md",
        "gdd.md",
    ]
    has_gdd, gdd_path, gdd_gaps = _find_markdown(root, gdd_patterns, min_chars=min_gdd_chars)
    if not has_gdd:
        gaps.extend(gdd_gaps)

    if gaps and "godot.project_missing" in gaps and not has_gdd:
        return {
            "ready": False,
            "detail": "Pas de project.godot ni GDD suffisant",
            "gaps": gaps,
            "godot_projects": 0,
            "gdd_path": gdd_path,
        }

    status_detail = []
    if godot_files:
        status_detail.append(f"Godot OK ({len(godot_files)} projet(s))")
    if has_gdd:
        status_detail.append(f"GDD OK ({gdd_path})")

    soft_gaps = [g for g in gaps if g != "godot.project_missing"]
    if "godot.project_missing" in gaps and has_gdd:
        return {
            "ready": True,
            "soft": True,
            "detail": " · ".join(status_detail) + " — Godot absent (pré-prod design only)",
            "gaps": ["godot.project_missing"],
            "godot_projects": 0,
            "gdd_path": gdd_path,
        }

    if soft_gaps:
        return {
            "ready": False,
            "detail": "Livrables gaming incomplets",
            "gaps": gaps,
            "godot_projects": len(godot_files),
            "gdd_path": gdd_path,
        }

    return {
        "ready": True,
        "detail": " · ".join(status_detail) if status_detail else "Gaming readiness OK",
        "gaps": [],
        "godot_projects": len(godot_files),
        "gdd_path": gdd_path,
    }


def check_robotics_readiness(
    local_path: str,
    *,
    slug: str = "",
    min_brief_chars: int = 100,
) -> dict[str, Any]:
    """Hardware brief / BOM sketch + optional firmware brief."""
    root = _project_root(local_path)
    if not root:
        return {
            "ready": False,
            "detail": f"Chemin introuvable : {local_path}",
            "gaps": ["local_path.missing"],
        }

    hw_patterns = [
        f"hardware/{slug}/hardware-brief.md" if slug else "hardware/*/hardware-brief.md",
        "hardware/**/bom*.md",
        "hardware/**/hardware*.md",
        "docs/bom.md",
        "BOM.md",
    ]
    has_hw, hw_path, hw_gaps = _find_markdown(root, hw_patterns, min_chars=min_brief_chars)

    fw_patterns = [
        f"hardware/{slug}/embedded-brief.md" if slug else "hardware/*/embedded-brief.md",
        "firmware/**/README.md",
        "embedded/**/README.md",
    ]
    has_fw, fw_path, _ = _find_markdown(root, fw_patterns, min_chars=60)

    gaps: list[str] = []
    if not has_hw:
        gaps.extend(hw_gaps)

    if not has_hw:
        return {
            "ready": False,
            "detail": "Brief hardware / BOM absent ou trop court",
            "gaps": gaps,
            "hardware_path": hw_path,
            "firmware_path": fw_path,
        }

    detail = f"Hardware OK ({hw_path})"
    soft: list[str] = []
    if not has_fw:
        soft.append("embedded_brief.missing")
        detail += " — firmware brief recommandé avant prod"

    return {
        "ready": True,
        "soft": bool(soft),
        "detail": detail,
        "gaps": soft,
        "hardware_path": hw_path,
        "firmware_path": fw_path,
    }


def validate_registry_for_branch(
    slug: str,
    *,
    required_branch: BranchKind,
) -> dict[str, Any]:
    from services.app_registry import get_app

    if not slug:
        return {"status": "ECART", "detail": "slug requis", "gaps": ["context.slug"]}

    entry = get_app(slug)
    if not entry:
        return {"status": "ECART", "detail": f"App '{slug}' absente du registry", "gaps": ["registry.slug"]}
    if not entry.enabled:
        return {"status": "ECART", "detail": f"App '{slug}' désactivée", "gaps": ["registry.disabled"]}
    if entry.branch != required_branch:
        return {
            "status": "ECART",
            "detail": f"Branche {entry.branch} — attendu {required_branch}",
            "gaps": [f"registry.branch.{entry.branch}"],
            "result": entry.model_dump(),
        }
    if not entry.path_exists:
        return {
            "status": "ECART",
            "detail": f"Chemin local introuvable : {entry.local_path}",
            "gaps": ["local_path.missing"],
            "result": entry.model_dump(),
        }
    return {
        "status": "OK",
        "detail": f"{entry.name} — {required_branch} · path OK",
        "result": {"slug": slug, "branch": entry.branch, "local_path": entry.local_path},
    }
