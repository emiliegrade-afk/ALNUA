"""Recent GitHub commits, pull requests, and releases for content agents.

Empty lists mean a scan ran and found nothing. A missing token or an
unreadable API is ``available: False`` — never the same shape as a quiet week.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

logger = logging.getLogger(__name__)

_GITHUB_API = "https://api.github.com"
_REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_TIMEOUT_S = 10.0


def fetch_repo_activity(repo: str, *, days: int = 7) -> dict[str, Any]:
    """Read one repository. ``repo`` may be ``owner/name`` or a configured slug."""
    scanned_at = datetime.now(timezone.utc).isoformat()
    window = max(1, min(int(days), 30))
    resolved = _resolve_repo(repo)
    token = os.getenv("GITHUB_TOKEN", "").strip()
    base = {
        "repo": repo,
        "resolved_repo": resolved,
        "days": window,
        "commits": [],
        "prs": [],
        "releases": [],
        "scanned_at": scanned_at,
        "source": "github",
    }
    if not token or not resolved:
        return {
            **base,
            "ok": False,
            "available": False,
            "note": "GITHUB_TOKEN ou dépôt non configuré — aucune activité lue.",
        }

    since = (datetime.now(timezone.utc) - timedelta(days=window)).strftime("%Y-%m-%dT%H:%M:%SZ")
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        with httpx.Client(timeout=_TIMEOUT_S) as client:
            commits = client.get(
                f"{_GITHUB_API}/repos/{resolved}/commits",
                headers=headers,
                params={"since": since, "per_page": 10},
            )
            pulls = client.get(
                f"{_GITHUB_API}/repos/{resolved}/pulls",
                headers=headers,
                params={"state": "all", "sort": "updated", "direction": "desc", "per_page": 10},
            )
            releases = client.get(
                f"{_GITHUB_API}/repos/{resolved}/releases",
                headers=headers,
                params={"per_page": 5},
            )
            commits.raise_for_status()
            pulls.raise_for_status()
            releases.raise_for_status()
    except Exception as exc:
        logger.warning("GitHub activity unread for %s: %s", resolved, exc)
        return {
            **base,
            "ok": False,
            "available": False,
            "note": "GitHub illisible — activité non lue.",
        }

    commit_rows = _as_list(commits.json())
    pr_rows = [
        row
        for row in _as_list(pulls.json())
        if str(row.get("updated_at") or "") >= since
    ]
    release_rows = [
        row
        for row in _as_list(releases.json())
        if str(row.get("published_at") or "") >= since
    ]
    return {
        **base,
        "ok": True,
        "available": True,
        "empty": not commit_rows and not pr_rows and not release_rows,
        "commits": [_slim_commit(row) for row in commit_rows],
        "prs": [_slim_pr(row) for row in pr_rows],
        "releases": [_slim_release(row) for row in release_rows],
        "note": f"Scan GitHub de {resolved} sur {window} jours.",
    }


def _resolve_repo(repo: str) -> str | None:
    raw = (repo or "").strip()
    if _REPO_RE.match(raw):
        return raw
    needle = raw.lower()
    try:
        from config.github_repos import get_repo_targets

        for target in get_repo_targets():
            names = {target.slug.lower(), target.name.lower(), target.github_repo.lower()}
            if needle and needle in names:
                return target.github_repo
    except Exception:
        logger.warning("Repo targets unread", exc_info=True)
    if needle in {"", "alnua", "aluna", "hub"}:
        env_repo = os.getenv("GITHUB_REPO", "").strip()
        if _REPO_RE.match(env_repo):
            return env_repo
    return None


def _as_list(payload: Any) -> list[dict[str, Any]]:
    if not isinstance(payload, list):
        return []
    return [row for row in payload if isinstance(row, dict)]


def _slim_commit(row: dict[str, Any]) -> dict[str, str]:
    commit = row.get("commit") if isinstance(row.get("commit"), dict) else {}
    message = str(commit.get("message") or "").split("\n", 1)[0][:120]
    author = commit.get("author") if isinstance(commit.get("author"), dict) else {}
    return {
        "sha": str(row.get("sha") or "")[:12],
        "message": message,
        "date": str(author.get("date") or ""),
        "url": str(row.get("html_url") or ""),
    }


def _slim_pr(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "number": row.get("number"),
        "title": str(row.get("title") or "")[:120],
        "state": str(row.get("state") or ""),
        "merged": bool(row.get("merged_at")),
        "updated_at": str(row.get("updated_at") or ""),
        "url": str(row.get("html_url") or ""),
    }


def _slim_release(row: dict[str, Any]) -> dict[str, str]:
    return {
        "tag": str(row.get("tag_name") or ""),
        "name": str(row.get("name") or "")[:120],
        "published_at": str(row.get("published_at") or ""),
        "url": str(row.get("html_url") or ""),
    }
