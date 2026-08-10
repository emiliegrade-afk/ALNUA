"""Build manifest persistence for PRD → GitHub issues."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from services.engineering_spec import EngineeringTask
from services.rnd_schemas import RndDossierOut
from services.rnd_workspace import workspace_root

logger = logging.getLogger(__name__)


def build_manifest_path(slug: str) -> str:
    return str(workspace_root() / f"{slug}.build.json")


def read_build_manifest(slug: str) -> dict[str, Any]:
    path = workspace_root() / f"{slug}.build.json"
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            logger.warning("build manifest corrompu: %s", slug)
    return {}


def write_build_manifest(slug: str, data: dict[str, Any]) -> str:
    path = workspace_root() / f"{slug}.build.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    return str(path)


def init_build_manifest(
    dossier: RndDossierOut,
    *,
    repo_slug: str,
    github_repo: str,
    tasks: list[EngineeringTask],
) -> dict[str, Any]:
    now = datetime.now(timezone.utc).isoformat()
    data: dict[str, Any] = {
        "slug": dossier.slug,
        "title": dossier.title,
        "dossier_id": dossier.id,
        "repo_slug": repo_slug,
        "github_repo": github_repo,
        "created_at": now,
        "updated_at": now,
        "progress_pct": 0.0,
        "issues_total": len(tasks),
        "issues_created": 0,
        "issues_done": 0,
        "issues_failed": 0,
        "issues_skipped": 0,
        "issues": [],
        "sprints": {},
    }
    write_build_manifest(dossier.slug, data)
    return data


def update_build_manifest_issues(
    slug: str,
    *,
    created: list[dict[str, Any]],
    skipped: list[str],
    repo_slug: str,
    github_repo: str,
) -> dict[str, Any]:
    data = read_build_manifest(slug) or {}
    issues = list(data.get("issues") or [])
    issues.extend(created)
    total = int(data.get("issues_total") or 0)
    done = int(data.get("issues_done") or 0)
    created_count = len([i for i in issues if i.get("number")])
    progress = round((done / total) * 100, 1) if total else 0.0

    data.update(
        {
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "repo_slug": repo_slug,
            "github_repo": github_repo,
            "issues": issues,
            "issues_created": created_count,
            "issues_skipped": len(skipped),
            "progress_pct": progress,
        }
    )
    write_build_manifest(slug, data)
    return data
