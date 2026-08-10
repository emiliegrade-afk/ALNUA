"""PRD → GitHub issues factory + build manifest (Phase 3)."""

from __future__ import annotations

import json
import logging
from typing import Any

from config.github_repos import resolve_target
from services.engineering_spec import EngineeringTask
from services.prd_issues_github import (  # noqa: F401 — re-export
    create_github_issue,
    format_issue_body,
    github_title,
    labels_for_task,
    list_existing_titles,
    resolve_repo_slug_for_dossier,
)
from services.prd_issues_manifest import (  # noqa: F401 — re-export
    build_manifest_path,
    init_build_manifest,
    read_build_manifest,
    update_build_manifest_issues,
    write_build_manifest,
)
from services.rnd_schemas import RndDossierOut
from services.rnd_workspace import write_deliverable

logger = logging.getLogger(__name__)


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
        task_labels = labels_for_task(task, mark_ready=mark_ready)

        if dry_run:
            created.append(
                {
                    "task_id": task.id,
                    "title": title,
                    "labels": task_labels,
                    "dry_run": True,
                }
            )
            continue

        issue = create_github_issue(
            github_repo=target.github_repo,
            title=title,
            body=body,
            labels=task_labels,
        )
        created.append(
            {
                "task_id": task.id,
                "number": issue["number"],
                "title": title,
                "url": issue.get("html_url"),
                "labels": task_labels,
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
        "build_manifest_path": build_manifest_path(dossier.slug),
        "manifest": manifest,
        "dry_run": dry_run,
    }
