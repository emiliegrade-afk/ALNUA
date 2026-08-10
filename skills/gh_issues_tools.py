"""GitHub Issues — CrewAI tools for agents (list/create/comment/label)."""

from __future__ import annotations

import httpx
from crewai.tools import tool

from config.github_repos import resolve_target
from skills.gh_issues_client import GITHUB_API, get_headers, github_get, post_comment, set_label


def _resolve_github_repo(repo_slug: str = "hub") -> str:
    target = resolve_target(repo_slug=repo_slug)
    return target.github_repo


@tool("get_open_issues")
def get_open_issues(repo_slug: str = "hub") -> str:
    """Liste les issues GitHub ouvertes sur un repo ALNUA (hub, academy, registry)."""
    try:
        target = resolve_target(repo_slug=repo_slug)
        url = f"{GITHUB_API}/repos/{target.github_repo}/issues"
        params = {"state": "open", "per_page": 20}

        with httpx.Client() as client:
            resp = github_get(client, url, params=params)
            issues = [
                issue
                for issue in resp.json()
                if "pull_request" not in issue
            ]

        if not issues:
            return f"Aucune issue ouverte sur {target.name} ({target.github_repo})."

        lines = [
            f"#{issue['number']} — {issue['title']} "
            f"[{', '.join(label['name'] for label in issue.get('labels', []))}]"
            for issue in issues
        ]
        return f"Issues ouvertes ({target.name}) :\n" + "\n".join(lines)
    except Exception as exc:
        return f"Erreur get_open_issues : {exc}"


@tool("create_github_issue")
def create_github_issue(
    title: str,
    body: str = "",
    repo_slug: str = "hub",
    labels: str = "",
) -> str:
    """Crée une issue GitHub. labels: noms séparés par des virgules (ex. agent-ready,bug)."""
    try:
        target = resolve_target(repo_slug=repo_slug)
        label_list = [label.strip() for label in labels.split(",") if label.strip()] if labels else []

        with httpx.Client() as client:
            resp = client.post(
                f"{GITHUB_API}/repos/{target.github_repo}/issues",
                headers=get_headers(),
                json={
                    "title": title,
                    "body": body or "Issue créée par un agent ALNUA.",
                    "labels": label_list,
                },
            )
            resp.raise_for_status()
            issue = resp.json()

        return (
            f"Issue #{issue['number']} créée sur {target.github_repo}\n"
            f"URL : {issue['html_url']}"
        )
    except Exception as exc:
        return f"Erreur create_github_issue : {exc}"


@tool("comment_on_issue")
def comment_on_issue(issue_number: int, body: str, repo_slug: str = "hub") -> str:
    """Poste un commentaire sur une issue GitHub."""
    try:
        github_repo = _resolve_github_repo(repo_slug)
        post_comment(issue_number, body, github_repo=github_repo)
        return f"Commentaire posté sur #{issue_number} ({github_repo})."
    except Exception as exc:
        return f"Erreur comment_on_issue : {exc}"


@tool("label_issue")
def label_issue(
    issue_number: int,
    add_labels: str,
    repo_slug: str = "hub",
    remove_labels: str = "",
) -> str:
    """Ajoute ou retire des labels sur une issue. Labels séparés par des virgules."""
    try:
        github_repo = _resolve_github_repo(repo_slug)
        add = [label.strip() for label in add_labels.split(",") if label.strip()]
        remove = [label.strip() for label in remove_labels.split(",") if label.strip()] or None
        set_label(
            issue_number,
            add,
            remove_labels=remove,
            github_repo=github_repo,
        )
        return f"Labels mis à jour sur #{issue_number} ({github_repo})."
    except Exception as exc:
        return f"Erreur label_issue : {exc}"
