"""GitHub Issues — fetch issues and open PRs across configured repos."""

from __future__ import annotations

import logging

import httpx

from config.github_repos import (
    GitHubRepoTarget,
    annotate_issue,
    get_repo_targets,
    resolve_target,
)
from skills.gh_issues_client import GITHUB_API, github_get

logger = logging.getLogger(__name__)


def _fetch_issue(issue_number: int, target: GitHubRepoTarget) -> dict:
    with httpx.Client() as client:
        resp = github_get(
            client,
            f"{GITHUB_API}/repos/{target.github_repo}/issues/{issue_number}",
        )
        return annotate_issue(resp.json(), target)


def get_issue(
    issue_number: int,
    *,
    repo_slug: str | None = None,
    github_repo: str | None = None,
) -> dict:
    """Récupère une issue GitHub par numéro (repo explicite ou recherche multi-repo)."""
    if repo_slug or github_repo:
        target = resolve_target(repo_slug=repo_slug, github_repo=github_repo)
        return _fetch_issue(issue_number, target)

    last_error: Exception | None = None
    for target in get_repo_targets():
        try:
            return _fetch_issue(issue_number, target)
        except httpx.HTTPStatusError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                last_error = exc
                continue
            raise

    raise ValueError(
        f"Issue #{issue_number} introuvable sur les repos configurés"
    ) from last_error


def _list_ready_for_target(target: GitHubRepoTarget) -> list[dict]:
    url = f"{GITHUB_API}/repos/{target.github_repo}/issues"
    params = {"labels": "agent-ready", "state": "open", "per_page": 10}

    with httpx.Client() as client:
        resp = github_get(client, url, params=params)
        issues = resp.json()

    ready = [
        issue
        for issue in issues
        if not any(label["name"] == "in-pipeline" for label in issue.get("labels", []))
        and "pull_request" not in issue
    ]
    return [annotate_issue(issue, target) for issue in ready]


def list_ready_issues() -> list[dict]:
    """Issues agent-ready sur tous les repos configurés."""
    targets = get_repo_targets()
    if not targets:
        raise ValueError("Aucun repo GitHub configuré (GITHUB_REPO, GITHUB_REPO_ACADEMY, …)")

    all_issues: list[dict] = []
    for target in targets:
        try:
            all_issues.extend(_list_ready_for_target(target))
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "[GHIssues] Impossible de lister %s : %s",
                target.github_repo,
                exc,
            )

    all_issues.sort(key=lambda issue: issue.get("created_at", ""), reverse=True)
    return all_issues


def get_open_prs() -> list[dict]:
    """PRs ouvertes agrégées depuis tous les repos configurés."""
    targets = get_repo_targets()
    if not targets:
        raise ValueError("Aucun repo GitHub configuré")

    all_prs: list[dict] = []
    for target in targets:
        url = f"{GITHUB_API}/repos/{target.github_repo}/pulls"
        params = {"state": "open", "per_page": 20}

        with httpx.Client() as client:
            resp = github_get(client, url, params=params)
            pulls = resp.json()

        all_prs.extend(
            {
                "number": pr["number"],
                "title": pr["title"],
                "url": pr["html_url"],
                "html_url": pr["html_url"],
                "branch": pr["head"]["ref"],
                "repo_slug": target.slug,
                "repo_name": target.name,
                "github_repo": target.github_repo,
                "repo_path": str(target.local_path),
                "auto": any(
                    label["name"] in ("agent-done", "agent-ready", "in-pipeline")
                    for label in pr.get("labels", [])
                ),
            }
            for pr in pulls
        )

    return all_prs
