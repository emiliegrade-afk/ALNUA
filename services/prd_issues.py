"""PRD → GitHub issues factory + build manifest (Phase 3)."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx

from config.github_repos import get_target_by_slug, resolve_target
from services.engineering_spec import EngineeringTask
from services.rnd_schemas import RndDossierOut
from services.rnd_workspace import workspace_root, write_deliverable

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
ISSUE_TITLE_PREFIX = "[AGENT]"


def _headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise ValueError("GITHUB_TOKEN manquant")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def resolve_repo_slug_for_dossier(
    dossier: RndDossierOut,
    *,
    repo_slug: str | None = None,
) -> str:
    """Pick GitHub target: explicit override → slug heuristics → nomad → hub."""
    if repo_slug:
        return repo_slug

    haystack = f"{dossier.slug} {dossier.title} {dossier.domain}".lower()
    if any(k in haystack for k in ("nomad", "nuaway", "vanlife", "park4")):
        if get_target_by_slug("nomad"):
            return "nomad"
    if "naia" in haystack and get_target_by_slug("naia"):
        return "naia"
    if get_target_by_slug("nomad"):
        return "nomad"
    if get_target_by_slug("hub"):
        return "hub"
    raise ValueError(
        "Aucun repo GitHub configuré — définir GITHUB_REPO_NOMAD ou GITHUB_REPO"
    )


def github_title(task: EngineeringTask, *, dossier_slug: str) -> str:
    base = task.title.strip()
    if base.upper().startswith("[AGENT]"):
        return base
    return f"{ISSUE_TITLE_PREFIX} [{dossier_slug}] {base}"


def format_issue_body(
    task: EngineeringTask,
    *,
    dossier_slug: str,
    dossier_title: str,
    extra_context: str = "",
) -> str:
    """agent_task.md compatible body."""
    lines = [
        "## Description",
        task.description or task.title,
        "",
        "## Stack",
        task.stack,
        "",
        "## Fichiers à créer",
    ]
    if task.files_create:
        lines.extend(f"- `{p}`" for p in task.files_create)
    else:
        lines.append("- _(aucun)_")
    lines.extend(["", "## Fichiers à modifier"])
    if task.files_modify:
        lines.extend(f"- `{p}`" for p in task.files_modify)
    else:
        lines.append("- _(aucun)_")
    lines.extend(["", "## Tests"])
    if task.tests:
        lines.extend(f"- `{t}`" for t in task.tests)
    else:
        lines.append("- _(à définir par l'agent)_")
    lines.extend(
        [
            "",
            "## Contexte additionnel",
            f"- Dossier : **{dossier_title}** (`{dossier_slug}`)",
            f"- Task ID : `{task.id}`",
            f"- Sprint : {task.sprint}",
            f"- Priorité : {task.priority}",
            f"- Agent cible : `{task.agent_id}`",
        ]
    )
    if task.depends_on:
        lines.append(f"- Dépend de : {', '.join(task.depends_on)}")
    if extra_context:
        lines.extend(["", extra_context.strip()])
    return "\n".join(lines)


def _labels_for_task(task: EngineeringTask, *, mark_ready: bool) -> list[str]:
    labels = ["prd", f"sprint-{task.sprint}", f"priority-{task.priority.lower()}"]
    if mark_ready:
        labels.append("agent-ready")
    return labels


def list_existing_titles(github_repo: str) -> set[str]:
    titles: set[str] = set()
    url = f"{GITHUB_API}/repos/{github_repo}/issues"
    page = 1
    with httpx.Client(timeout=30.0) as client:
        while page <= 10:
            resp = client.get(
                url,
                headers=_headers(),
                params={"state": "all", "per_page": 100, "page": page},
            )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            for issue in batch:
                if "pull_request" not in issue:
                    titles.add(issue.get("title", ""))
            if len(batch) < 100:
                break
            page += 1
    return titles


def create_github_issue(
    *,
    github_repo: str,
    title: str,
    body: str,
    labels: list[str],
) -> dict[str, Any]:
    url = f"{GITHUB_API}/repos/{github_repo}/issues"
    payload = {"title": title, "body": body, "labels": labels}
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, headers=_headers(), json=payload)
        resp.raise_for_status()
        return resp.json()


def _build_manifest_path(slug: str) -> str:
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


def publish_tasks_to_github(
    dossier: RndDossierOut,
    tasks: list[EngineeringTask],
    *,
    repo_slug: str | None = None,
    dry_run: bool = False,
    mark_ready_count: int = 3,
    extra_context: str = "",
) -> dict[str, Any]:
    """
    Create GitHub issues from engineering task breakdown (idempotent by title).
    First N issues of sprint 1 P0 get agent-ready label.
    """
    slug = resolve_repo_slug_for_dossier(dossier, repo_slug=repo_slug)
    target = resolve_target(repo_slug=slug)
    existing = list_existing_titles(target.github_repo) if not dry_run else set()

    init_build_manifest(
        dossier,
        repo_slug=slug,
        github_repo=target.github_repo,
        tasks=tasks,
    )

    created: list[dict[str, Any]] = []
    skipped: list[str] = []
    ready_budget = max(0, mark_ready_count)

    # Sort: sprint asc, P0 first
    priority_order = {"P0": 0, "P1": 1, "P2": 2}
    sorted_tasks = sorted(
        tasks,
        key=lambda t: (t.sprint, priority_order.get(t.priority.upper(), 9), t.id),
    )

    for task in sorted_tasks:
        title = github_title(task, dossier_slug=dossier.slug)
        if title in existing:
            skipped.append(task.id)
            continue

        mark_ready = ready_budget > 0 and task.priority.upper() == "P0" and task.sprint == 1
        if mark_ready:
            ready_budget -= 1

        body = format_issue_body(
            task,
            dossier_slug=dossier.slug,
            dossier_title=dossier.title,
            extra_context=extra_context,
        )
        labels = _labels_for_task(task, mark_ready=mark_ready)

        if dry_run:
            created.append(
                {
                    "task_id": task.id,
                    "title": title,
                    "labels": labels,
                    "dry_run": True,
                }
            )
            continue

        issue = create_github_issue(
            github_repo=target.github_repo,
            title=title,
            body=body,
            labels=labels,
        )
        created.append(
            {
                "task_id": task.id,
                "number": issue["number"],
                "title": title,
                "url": issue.get("html_url"),
                "labels": labels,
                "state": "open",
            }
        )
        existing.add(title)

    manifest = update_build_manifest_issues(
        dossier.slug,
        created=created,
        skipped=skipped,
        repo_slug=slug,
        github_repo=target.github_repo,
    )

    # Persist task breakdown on disk for agents
    try:
        write_deliverable(
            "direction",
            dossier.slug,
            "engineering-spec-tasks.json",
            json.dumps(
                {
                    "dossier_id": dossier.id,
                    "repo_slug": slug,
                    "github_repo": target.github_repo,
                    "tasks": [t.model_dump() for t in tasks],
                    "issues_created": created,
                },
                indent=2,
                ensure_ascii=False,
            ),
        )
    except Exception as exc:
        logger.warning("write engineering-spec-tasks.json failed: %s", exc)

    return {
        "repo_slug": slug,
        "github_repo": target.github_repo,
        "created_count": len(created),
        "skipped_count": len(skipped),
        "created": created,
        "skipped": skipped,
        "build_manifest_path": _build_manifest_path(dossier.slug),
        "manifest": manifest,
        "dry_run": dry_run,
    }
