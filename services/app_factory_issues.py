"""GitHub issue helpers for App Factory."""

from __future__ import annotations

from typing import Any

import httpx

from config.github_repos import GitHubRepoTarget, annotate_issue
from services.app_factory_models import GITHUB_API, FactoryTask, _FACTORY_STACK, stack_value


def github_headers() -> dict[str, str]:
    from skills.skill_gh_issues import get_headers

    return get_headers()


def create_issue_on_repo(
    target: GitHubRepoTarget,
    *,
    title: str,
    body: str,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Create a GitHub issue and return annotated issue dict."""
    with httpx.Client() as client:
        resp = client.post(
            f"{GITHUB_API}/repos/{target.github_repo}/issues",
            headers=github_headers(),
            json={
                "title": title,
                "body": body,
                "labels": labels or [],
            },
            timeout=30.0,
        )
        resp.raise_for_status()
        return annotate_issue(resp.json(), target)


def format_issue_body(task: FactoryTask, stack: _FACTORY_STACK) -> str:
    """Markdown body parsed by skill_gh_issues.issue_to_spec."""
    create_lines = "\n".join(f"- {p}" for p in task.files_to_create) or "- <!-- à définir -->"
    modify_lines = "\n".join(f"- {p}" for p in task.files_to_modify) or "- <!-- aucun -->"
    test_lines = "\n".join(f"- {t}" for t in task.tests_to_pass) or "- npm run build"
    return (
        f"## Description\n{task.description.strip()}\n\n"
        f"## Stack\n{stack_value(stack)}\n\n"
        f"## Fichiers à créer\n{create_lines}\n\n"
        f"## Fichiers à modifier\n{modify_lines}\n\n"
        f"## Tests\n{test_lines}\n"
    )
