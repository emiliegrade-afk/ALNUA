"""Multi-repo watchdog coverage — maps app registry to fix_pipeline repo paths."""

from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger(__name__)


def build_repo_path_map() -> dict[str, str]:
    """slug → local_path for all enabled registry apps + hub."""
    from services.app_registry import list_apps

    mapping: dict[str, str] = {}
    for app in list_apps(include_disabled=False):
        if app.local_path and app.path_exists:
            mapping[app.slug] = app.local_path
    hub_path = os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB")
    mapping.setdefault("hub", hub_path)
    return mapping


def resolve_repo_path_for_slug(slug: str | None, agent_name: str = "") -> tuple[str, str | None]:
    """Return (local_path, github_repo) for an error's repo_slug or agent fallback."""
    from config.github_repos import get_repo_targets
    from services.app_registry import get_app

    if slug:
        entry = get_app(slug)
        if entry and entry.local_path and entry.path_exists:
            return entry.local_path, entry.github_repo or None

    # Agent → repo fallback when repo_slug unknown (hub + academy only)
    hub_path = os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB")
    academy_path = os.getenv("REPO_PATH_ACADEMY", "C:/Dev/alnua-academy")
    resonance_path = os.getenv("REPO_PATH_RESONANCE", "C:/Dev/RESONANCE")
    agent_paths: dict[str, str] = {
        "dev_app": academy_path,
        "dev_resonance": resonance_path,
        "dev_gaming": hub_path,
        "embedded": hub_path,
        "coo": hub_path,
        "pm_agent": hub_path,
        "qa_agent": hub_path,
        "spec_agent": hub_path,
    }
    if slug == "resonance":
        github_repo = None
        try:
            for target in get_repo_targets():
                if target.slug == "resonance":
                    return str(target.local_path), target.github_repo
        except Exception:
            pass
        return resonance_path, None

    repo_path = agent_paths.get(agent_name, hub_path)

    github_repo = None
    try:
        for target in get_repo_targets():
            if target.local_path and repo_path.startswith(str(target.local_path)):
                github_repo = target.github_repo
                break
    except Exception:
        pass

    return repo_path, github_repo


def build_watchdog_coverage_report() -> dict[str, Any]:
    """Summarize which registry apps are covered by watchdog path resolution."""
    from services.app_registry import list_apps
    from services.company_errors import count_open_errors

    apps = [a for a in list_apps(include_disabled=False) if a.slug != "hub"]
    mapped: list[dict[str, Any]] = []
    unmapped: list[str] = []

    for app in apps:
        path, _gh = resolve_repo_path_for_slug(app.slug)
        open_err = count_open_errors(repo_slug=app.slug)
        item = {
            "slug": app.slug,
            "branch": app.branch,
            "path_exists": app.path_exists,
            "watchdog_path": path,
            "open_errors": open_err,
            "lifecycle_status": getattr(app, "lifecycle_status", "build"),
        }
        if app.path_exists:
            mapped.append(item)
        else:
            unmapped.append(app.slug)

    total_open = sum(m["open_errors"] for m in mapped)
    summary = (
        f"{len(mapped)} repo(s) mappé(s), {len(unmapped)} sans path local, "
        f"{total_open} erreur(s) ouverte(s)"
    )
    return {
        "summary": summary,
        "mapped": mapped,
        "unmapped_slugs": unmapped,
        "total_open_errors": total_open,
        "watchdog_enabled": os.getenv("WATCHDOG_ENABLED", "true").lower() not in ("0", "false", "no"),
    }
