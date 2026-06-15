"""Canonical project paths — avoids hardcoded Windows defaults scattered in the codebase."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent


@lru_cache
def get_project_root() -> Path:
    return _PROJECT_ROOT


@lru_cache
def get_hub_repo_path() -> Path:
    from config.settings import get_settings

    configured = get_settings().hub_repo_path.strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return _PROJECT_ROOT


def data_dir(name: str) -> Path:
    """Return ``data/{name}`` under the hub repo root."""
    return get_hub_repo_path() / "data" / name


@lru_cache
def get_alnua_workspace() -> Path:
    """Workspace disque pour livrables R&D pôles.

    Ordre de résolution :
    1. ``ALNUA_WORKSPACE`` dans .env
    2. Fallback : ``C:/Dev/ALNUA`` (Windows) / ``~/Dev/ALNUA`` (autre OS)
    """
    from config.settings import get_settings
    import platform

    configured = get_settings().alnua_workspace.strip()
    if configured:
        return Path(configured).expanduser().resolve()
    if platform.system() == "Windows":
        return Path("C:/Dev/ALNUA").resolve()
    return Path.home() / "Dev" / "ALNUA"
