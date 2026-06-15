"""Workspace disque pour livrables R&D.

Convention : ALNUA_WORKSPACE/{pole}/{slug}/{filename}
- direction/{slug}/spec-cursor-prompt.md
- app/{slug}/tech-brief.md
- comms/{slug}/gtm-strategy.md
etc.

Manifest : ALNUA_WORKSPACE/{slug}.manifest.json (a la racine du workspace)
- write-only (jamais de suppression)
"""

from __future__ import annotations

import json
import logging
import os
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

WORKSPACE_POLES = [
    "direction", "app", "gaming", "comms",
    "finance", "hardware", "innovation", "analytics",
]


def _workspace_root() -> Path:
    """Resout ALNUA_WORKSPACE — os.environ en premier, puis config.paths (fallback)."""
    raw = os.environ.get("ALNUA_WORKSPACE", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    try:
        from config.paths import get_alnua_workspace
        return get_alnua_workspace()
    except Exception:
        if platform.system() == "Windows":
            return Path("C:/Dev/ALNUA").resolve()
        return Path.home() / "Dev" / "ALNUA"


def workspace_root() -> Path:
    return _workspace_root()


# ---------------------------------------------------------------------------
# Init
# ---------------------------------------------------------------------------

def init_project_workspace(slug: str) -> dict[str, Path]:
    """Cree ALNUA/{pole}/{slug}/ pour chaque pole.

    Convention Option A : pole en premier, slug en second.
    Retourne dict {pole: Path} pour chaque pole cree.
    Idempotent.
    """
    ws = _workspace_root()
    paths: dict[str, Path] = {}
    for pole in WORKSPACE_POLES:
        p = ws / pole / slug
        p.mkdir(parents=True, exist_ok=True)
        paths[pole] = p
    logger.info("Workspace initialise (Option A): %s/{pole}/%s/", ws, slug)
    return paths


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def pole_path(pole: str, slug: str) -> Path:
    """ALNUA/{pole}/{slug}/"""
    return _workspace_root() / pole / slug


def project_poles(slug: str) -> dict[str, Path]:
    """Dict {pole: Path} pour un projet."""
    ws = _workspace_root()
    return {pole: ws / pole / slug for pole in WORKSPACE_POLES}


# ---------------------------------------------------------------------------
# Write / Read
# ---------------------------------------------------------------------------

def write_deliverable(pole: str, slug: str, filename: str, content: str) -> Path:
    """Ecrit un livrable dans ALNUA/{pole}/{slug}/{filename}."""
    path = pole_path(pole, slug) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    logger.info("Livrable ecrit : %s (%d chars)", path, len(content))
    return path


def read_deliverable(pole: str, slug: str, filename: str) -> str | None:
    path = pole_path(pole, slug) / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return None


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_deliverables(slug: str, required_files: list[str]) -> dict[str, bool]:
    """Verifie que chaque fichier requis existe.

    Format de required_files : "pole/filename"
    -> verifie ALNUA/{pole}/{slug}/{filename}

    Exemple : "direction/spec-cursor-prompt.md"
    -> ALNUA/direction/{slug}/spec-cursor-prompt.md
    """
    ws = _workspace_root()
    result: dict[str, bool] = {}
    for f in required_files:
        if "/" in f:
            pole, filename = f.split("/", 1)
            result[f] = (ws / pole / slug / filename).exists()
        else:
            # Pas de pole specifie : cherche dans tous les poles
            result[f] = any((ws / pole / slug / f).exists() for pole in WORKSPACE_POLES)
    return result


def all_deliverables_present(slug: str, required_files: list[str]) -> bool:
    return all(validate_deliverables(slug, required_files).values())


def missing_deliverables(slug: str, required_files: list[str]) -> list[str]:
    checks = validate_deliverables(slug, required_files)
    return [f for f, exists in checks.items() if not exists]


# ---------------------------------------------------------------------------
# Manifest JSON
# ---------------------------------------------------------------------------

def _manifest_path(slug: str) -> Path:
    """Manifest a la racine du workspace : ALNUA/{slug}.manifest.json"""
    return _workspace_root() / f"{slug}.manifest.json"


def read_manifest(slug: str) -> dict[str, Any]:
    path = _manifest_path(slug)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("Manifest corrompu pour %s", slug)
    return {}


def write_manifest(slug: str, data: dict[str, Any]) -> Path:
    path = _manifest_path(slug)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def init_manifest(
    slug: str,
    title: str,
    workspace_root_path: Path,
    matrix: list[dict[str, Any]],
) -> dict[str, Any]:
    """Cree et ecrit le manifest initial."""
    data: dict[str, Any] = {
        "slug": slug,
        "title": title,
        "workspace_root": str(workspace_root_path),
        "convention": "ALNUA/{pole}/{slug}/{filename}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "poles": {
            pole: {
                "status": "pending",
                "path": str(workspace_root_path / pole / slug),
                "files": [],
            }
            for pole in WORKSPACE_POLES
        },
        "agents": {
            row.get("agent_id", ""): {
                "status": "pending",
                "deliverables": [],
                "pole": row.get("pole", ""),
            }
            for row in matrix
            if row.get("agent_id")
        },
        "validation": {
            "status": "pending",
            "missing_files": [],
            "completed_at": None,
        },
    }
    write_manifest(slug, data)
    return data


def update_manifest_agent(
    slug: str,
    agent_id: str,
    *,
    status: str,
    files: list[str] | None = None,
    error: str | None = None,
) -> None:
    try:
        data = read_manifest(slug)
        agents = data.setdefault("agents", {})
        entry = agents.setdefault(agent_id, {"status": "pending", "deliverables": []})
        entry["status"] = status
        if files:
            existing = set(entry.get("deliverables") or [])
            existing.update(files)
            entry["deliverables"] = sorted(existing)
        if error:
            entry["error"] = error[:500]
        entry["updated_at"] = datetime.now(timezone.utc).isoformat()
        write_manifest(slug, data)
    except Exception as exc:
        logger.warning("update_manifest_agent failed: %s", exc)


def finalize_manifest(
    slug: str,
    *,
    success: bool,
    missing: list[str] | None = None,
) -> None:
    try:
        data = read_manifest(slug)
        data["validation"] = {
            "status": "success" if success else "partial",
            "missing_files": missing or [],
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        write_manifest(slug, data)
    except Exception as exc:
        logger.warning("finalize_manifest failed: %s", exc)
