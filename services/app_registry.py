"""Central registry of ALNUA codebases — env targets + JSON overrides."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field

from config.github_repos import GitHubRepoTarget, get_repo_targets
from config.paths import get_hub_repo_path

logger = logging.getLogger(__name__)

_BRANCHES = Literal["app", "gaming", "robotics", "hub", "other"]
_LIFECYCLE = Literal["idea", "build", "beta", "prod"]
_REGISTRY_PATH = get_hub_repo_path() / "data" / "apps_registry.json"


class AppRegistryEntry(BaseModel):
    slug: str
    name: str
    branch: _BRANCHES = "app"
    github_repo: str = ""
    local_path: str = ""
    description: str = ""
    stack: str = ""
    prod_url: str = ""
    lifecycle_status: _LIFECYCLE = "build"
    enabled: bool = True
    source: str = "registry"  # env | registry | merged
    path_exists: bool = False
    github_configured: bool = False


class AppRegistryUpsert(BaseModel):
    slug: str = Field(..., min_length=1, max_length=64)
    name: str = Field(..., min_length=1, max_length=120)
    branch: _BRANCHES = "app"
    github_repo: str = ""
    local_path: str = ""
    description: str = ""
    stack: str = ""
    prod_url: str = ""
    lifecycle_status: _LIFECYCLE = "build"
    enabled: bool = True


def _slugify(value: str) -> str:
    import re

    s = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    return s or "app"


def _load_json_overrides() -> dict[str, dict[str, Any]]:
    try:
        if _REGISTRY_PATH.exists():
            raw = json.loads(_REGISTRY_PATH.read_text(encoding="utf-8"))
            items = raw.get("apps", raw) if isinstance(raw, dict) else raw
            if isinstance(items, list):
                return {str(a.get("slug", "")): a for a in items if a.get("slug")}
    except Exception as exc:
        logger.debug("apps_registry load failed: %s", exc)
    return {}


def _save_json_overrides(overrides: dict[str, dict[str, Any]]) -> None:
    _REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "apps": sorted(overrides.values(), key=lambda a: a.get("slug", "")),
    }
    _REGISTRY_PATH.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _target_to_entry(target: GitHubRepoTarget, *, source: str) -> AppRegistryEntry:
    branch = "hub" if target.slug == "hub" else "app"
    if target.slug == "academy":
        branch = "app"
    return AppRegistryEntry(
        slug=target.slug,
        name=target.name,
        branch=branch,  # type: ignore[arg-type]
        github_repo=target.github_repo,
        local_path=str(target.local_path),
        source=source,
        path_exists=target.local_path.exists(),
        github_configured=bool(target.github_repo),
        enabled=True,
    )


def _merge_entry(base: AppRegistryEntry, override: dict[str, Any]) -> AppRegistryEntry:
    data = base.model_dump()
    for key in (
        "name",
        "branch",
        "github_repo",
        "local_path",
        "description",
        "stack",
        "prod_url",
        "lifecycle_status",
        "enabled",
    ):
        if key in override and override[key] not in (None, ""):
            data[key] = override[key]
    data["source"] = "merged"
    path = Path(str(data.get("local_path") or ""))
    data["path_exists"] = path.exists() if str(path) else False
    data["github_configured"] = bool(str(data.get("github_repo") or "").strip())
    return AppRegistryEntry(**data)


def list_apps(*, include_disabled: bool = True) -> list[AppRegistryEntry]:
    """Merge .env repo targets with data/apps_registry.json."""
    overrides = _load_json_overrides()
    by_slug: dict[str, AppRegistryEntry] = {}

    for target in get_repo_targets():
        by_slug[target.slug] = _target_to_entry(target, source="env")

    for slug, raw in overrides.items():
        if slug in by_slug:
            by_slug[slug] = _merge_entry(by_slug[slug], raw)
        else:
            entry = AppRegistryEntry(
                slug=slug,
                name=str(raw.get("name") or slug),
                branch=raw.get("branch") or "app",
                github_repo=str(raw.get("github_repo") or ""),
                local_path=str(raw.get("local_path") or ""),
                description=str(raw.get("description") or ""),
                stack=str(raw.get("stack") or ""),
                prod_url=str(raw.get("prod_url") or ""),
                lifecycle_status=raw.get("lifecycle_status") or "build",
                enabled=bool(raw.get("enabled", True)),
                source="registry",
            )
            path = Path(entry.local_path)
            entry.path_exists = path.exists() if entry.local_path else False
            entry.github_configured = bool(entry.github_repo)
            by_slug[slug] = entry

    items = list(by_slug.values())
    if not include_disabled:
        items = [a for a in items if a.enabled]
    return sorted(items, key=lambda a: (a.branch, a.name.lower()))


def get_app(slug: str) -> AppRegistryEntry | None:
    for entry in list_apps():
        if entry.slug == slug:
            return entry
    return None


def upsert_app(body: AppRegistryUpsert) -> AppRegistryEntry:
    slug = _slugify(body.slug)
    overrides = _load_json_overrides()
    overrides[slug] = {
        **body.model_dump(),
        "slug": slug,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_json_overrides(overrides)
    entry = get_app(slug)
    if not entry:
        raise ValueError(f"Failed to persist app {slug}")
    return entry


def remove_app(slug: str) -> bool:
    overrides = _load_json_overrides()
    if slug not in overrides:
        return False
    del overrides[slug]
    _save_json_overrides(overrides)
    return True


def registry_summary() -> dict[str, Any]:
    apps = list_apps()
    return {
        "total": len(apps),
        "enabled": sum(1 for a in apps if a.enabled),
        "with_github": sum(1 for a in apps if a.github_configured),
        "with_local_path": sum(1 for a in apps if a.path_exists),
        "branches": {
            b: sum(1 for a in apps if a.branch == b)
            for b in ("hub", "app", "gaming", "robotics", "other")
        },
        "lifecycle": {
            s: sum(1 for a in apps if a.lifecycle_status == s)
            for s in ("idea", "build", "beta", "prod")
        },
    }
