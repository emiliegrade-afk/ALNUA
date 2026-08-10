"""GitHub issue helpers for PRD → issues factory."""

from __future__ import annotations

import os
from typing import Any

import httpx

from config.github_repos import get_target_by_slug
from services.engineering_spec import EngineeringTask
from services.rnd_schemas import RndDossierOut

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
    """Pick GitHub target: explicit override → registry match → hub."""
    if repo_slug:
        return repo_slug

    slug = (dossier.slug or "").strip().lower()
    if slug and get_target_by_slug(slug):
        return slug

    if get_target_by_slug("hub"):
        return "hub"
    if get_target_by_slug("academy"):
        return "academy"
    raise ValueError(
        "Aucun repo GitHub configuré — définir GITHUB_REPO ou enregistrer l'app dans le registry"
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


def labels_for_task(task: EngineeringTask, *, mark_ready: bool) -> list[str]:
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
