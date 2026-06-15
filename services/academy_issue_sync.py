"""Sync GitHub academy issues — close on merge, advance curriculum."""

from __future__ import annotations

import logging
import os
import re
from typing import Any

import httpx

from config.github_repos import get_target_by_slug

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
_ACADEMY_ID_RE = re.compile(r"^\[ACADEMY\s+(N\d+\.\d+)\]", re.I)


def _headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise ValueError("GITHUB_TOKEN manquant")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def close_issue(issue_number: int, *, github_repo: str, comment: str | None = None) -> bool:
    """Close a GitHub issue (optional comment)."""
    with httpx.Client() as client:
        if comment:
            client.post(
                f"{GITHUB_API}/repos/{github_repo}/issues/{issue_number}/comments",
                headers=_headers(),
                json={"body": comment},
            )
        resp = client.patch(
            f"{GITHUB_API}/repos/{github_repo}/issues/{issue_number}",
            headers=_headers(),
            json={"state": "closed"},
        )
        return resp.status_code == 200


def close_agent_done_issues(*, github_repo: str | None = None) -> dict[str, Any]:
    """Close open issues labeled agent-done (merged manually or via auto-merge)."""
    target = get_target_by_slug("academy")
    repo = github_repo or (target.github_repo if target else "")
    if not repo:
        return {"closed": [], "error": "academy repo not configured"}

    closed: list[dict[str, Any]] = []
    url = f"{GITHUB_API}/repos/{repo}/issues"
    params = {"state": "open", "per_page": 100, "labels": "agent-done"}

    with httpx.Client() as client:
        resp = client.get(url, headers=_headers(), params=params)
        resp.raise_for_status()
        for issue in resp.json():
            if "pull_request" in issue:
                continue
            num = issue["number"]
            if close_issue(
                num,
                github_repo=repo,
                comment="[BOT] Exercice validé — issue fermée après merge/QA.",
            ):
                closed.append({"number": num, "title": issue.get("title", "")})

    return {"closed_count": len(closed), "closed": closed, "github_repo": repo}


def advance_curriculum_if_level_complete() -> dict[str, Any]:
    """
    When current level is fully done, seed next level issues and mark first ready.
    """
    from services.academy_progress import load_progress
    from services.academy_seed import mark_next_agent_ready, seed_level

    progress = load_progress()
    current = int(progress.get("current_level") or 1)
    levels = progress.get("levels") or {}
    lv_key = str(current)
    lv_data = levels.get(lv_key) or {}
    done = int(lv_data.get("done") or 0)
    total = int(lv_data.get("total") or 0)
    in_prog = int(lv_data.get("in_progress") or 0)

    result: dict[str, Any] = {
        "current_level": current,
        "done": done,
        "total": total,
        "in_progress": in_prog,
        "advanced": False,
    }

    if done < total or in_prog > 0:
        return result

    next_level = current + 1
    if next_level > 4:
        result["message"] = "curriculum_complete"
        return result

    seed = seed_level(next_level, dry_run=False, mark_first_ready=False)
    ready = mark_next_agent_ready(level=next_level, count=2)
    result.update(
        {
            "advanced": True,
            "next_level": next_level,
            "seed": seed,
            "agent_ready": ready,
        }
    )
    logger.info("[AcademySync] Level %s complete → seeded N%s", current, next_level)
    return result


def run_academy_sync() -> dict[str, Any]:
    """Full sync: GitHub progress + close done issues + maybe advance level."""
    from services.academy_progress import get_academy_status

    status = get_academy_status()
    closed = close_agent_done_issues()
    advance = advance_curriculum_if_level_complete()
    return {
        "progress": status.get("progress"),
        "github_issues_count": status.get("github_issues_count"),
        "closed_issues": closed,
        "curriculum": advance,
    }
