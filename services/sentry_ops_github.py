"""GitHub hotfix issue creation for Sentry production alerts."""

from __future__ import annotations

import os
import re
from typing import Any

import httpx

from config.github_repos import resolve_target
from services.sentry_ops_parse import SentryIngestEvent

GITHUB_API = "https://api.github.com"
_ISSUE_PREFIX = "[HOTFIX]"


def _github_headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise ValueError("GITHUB_TOKEN manquant")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _issue_title(event: SentryIngestEvent) -> str:
    base = event.title.strip()
    if base.upper().startswith(_ISSUE_PREFIX):
        return base[:120]
    short = re.sub(r"\s+", " ", base)[:80]
    return f"{_ISSUE_PREFIX} [sentry] {short}"


def _stack_hint(event: SentryIngestEvent, repo_slug: str) -> str:
    platform = (event.platform or "").lower()
    if platform in ("javascript", "node", "react-native"):
        return "react_native_expo"
    if repo_slug == "hub":
        return "python_fastapi"
    if repo_slug in ("academy",):
        return "react_native_expo"
    return "python_fastapi"


def format_hotfix_issue_body(
    event: SentryIngestEvent,
    *,
    repo_slug: str,
    github_repo: str,
    journal_id: str | None,
) -> str:
    lines = [
        "## Description",
        f"Erreur production Sentry — **{event.level}**",
        "",
        event.message,
        "",
        "## Stack",
        _stack_hint(event, repo_slug),
        "",
        "## Contexte Sentry",
        f"- Environment : `{event.environment}`",
        f"- Project : `{event.project_slug or '—'}`",
        f"- Culprit : `{event.culprit or '—'}`",
        f"- Fingerprint : `{event.fingerprint}`",
    ]
    if event.permalink:
        lines.append(f"- Lien : {event.permalink}")
    if journal_id:
        lines.append(f"- Error journal : `{journal_id}`")
    lines.extend(["", "## Stacktrace", "```", event.stacktrace or "(non disponible)", "```"])
    lines.extend(
        [
            "",
            "## Fichiers à modifier",
            "- _(à identifier par l'agent — voir culprit / stacktrace)_",
            "",
            "## Tests",
            "- Reproduire le scénario + test de non-régression",
            "",
            "## Contexte additionnel",
            f"- Repo : `{github_repo}` (`{repo_slug}`)",
            "- Source : Sentry webhook → fix_pipeline",
            "- Priorité : hotfix production",
        ]
    )
    return "\n".join(lines)


def create_hotfix_github_issue(
    event: SentryIngestEvent,
    *,
    repo_slug: str,
    journal_id: str | None,
    mark_agent_ready: bool = True,
) -> dict[str, Any]:
    target = resolve_target(repo_slug=repo_slug)
    labels = ["sentry", "hotfix", "prod", f"severity-{event.level}"]
    if mark_agent_ready:
        labels.append("agent-ready")

    body = format_hotfix_issue_body(
        event,
        repo_slug=repo_slug,
        github_repo=target.github_repo,
        journal_id=journal_id,
    )
    url = f"{GITHUB_API}/repos/{target.github_repo}/issues"
    payload = {"title": _issue_title(event), "body": body, "labels": labels}
    with httpx.Client(timeout=30.0) as client:
        resp = client.post(url, headers=_github_headers(), json=payload)
        resp.raise_for_status()
        issue = resp.json()
    return {
        "number": issue["number"],
        "title": issue["title"],
        "url": issue.get("html_url"),
        "repo_slug": repo_slug,
        "github_repo": target.github_repo,
    }
