"""GitHub issue seeding for ALNUA Academy."""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

import httpx

from config.github_repos import get_target_by_slug
from services.academy_curriculum import AcademyExercise, exercises_for_level

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
_ACADEMY_ID_RE = re.compile(r"\[ACADEMY\s+(N\d+\.\d+)\]", re.I)


def _academy_issue_order(issue: dict) -> tuple[int, int]:
    """Order exercises N1.1 → N1.10 → N2.1 (not GitHub issue number)."""
    m = _ACADEMY_ID_RE.search(issue.get("title") or "")
    if not m:
        return (999, 999)
    from services.academy_curriculum import exercise_by_id

    ex = exercise_by_id(m.group(1).upper())
    if not ex:
        return (999, 999)
    level_str, num_str = ex.exercise_id[1:].split(".", 1)
    return (int(level_str), int(num_str))


def _headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise ValueError("GITHUB_TOKEN manquant")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _list_existing_titles(github_repo: str) -> set[str]:
    titles: set[str] = set()
    url = f"{GITHUB_API}/repos/{github_repo}/issues"
    params = {"state": "all", "per_page": 100}
    with httpx.Client() as client:
        resp = client.get(url, headers=_headers(), params=params)
        resp.raise_for_status()
        for issue in resp.json():
            if "pull_request" not in issue:
                titles.add(issue.get("title", ""))
    return titles


def create_academy_issue(
    exercise: AcademyExercise,
    *,
    github_repo: str,
    labels: list[str] | None = None,
) -> dict[str, Any]:
    """Create one GitHub issue for an academy exercise."""
    issue_labels = labels or ["academy", f"level-{exercise.level}"]
    payload = {
        "title": exercise.github_title(),
        "body": exercise.issue_body(),
        "labels": issue_labels,
    }
    url = f"{GITHUB_API}/repos/{github_repo}/issues"
    with httpx.Client() as client:
        resp = client.post(url, headers=_headers(), json=payload)
        resp.raise_for_status()
        return resp.json()


def seed_level(
    level: int,
    *,
    dry_run: bool = False,
    mark_first_ready: bool = False,
) -> dict[str, Any]:
    """
    Create GitHub issues for a curriculum level (idempotent by title).
    If mark_first_ready, label first open issue agent-ready.
    """
    target = get_target_by_slug("academy")
    if not target:
        raise ValueError(
            "Repo academy non configuré — définir GITHUB_REPO_ACADEMY dans .env"
        )

    exercises = exercises_for_level(level)
    if not exercises:
        raise ValueError(f"Niveau invalide : {level}")

    existing = _list_existing_titles(target.github_repo)
    created: list[dict[str, Any]] = []
    skipped: list[str] = []

    for ex in exercises:
        title = ex.github_title()
        if title in existing:
            skipped.append(ex.exercise_id)
            continue
        if dry_run:
            created.append({"exercise_id": ex.exercise_id, "title": title, "dry_run": True})
            continue
        issue = create_academy_issue(ex, github_repo=target.github_repo)
        created.append(
            {
                "exercise_id": ex.exercise_id,
                "number": issue["number"],
                "url": issue["html_url"],
            }
        )
        existing.add(title)

    first_ready: dict[str, Any] | None = None
    if mark_first_ready and not dry_run:
        first_ready = mark_next_agent_ready(level=level)

    return {
        "level": level,
        "dry_run": dry_run,
        "created_count": len(created),
        "skipped_count": len(skipped),
        "created": created,
        "skipped": skipped,
        "first_agent_ready": first_ready,
        "github_repo": target.github_repo,
    }


def mark_next_agent_ready(*, level: int | None = None, count: int = 1) -> dict[str, Any]:
    """Add agent-ready label to next open academy issues without it."""
    target = get_target_by_slug("academy")
    if not target:
        raise ValueError("GITHUB_REPO_ACADEMY non configuré")

    url = f"{GITHUB_API}/repos/{target.github_repo}/issues"
    params = {"state": "open", "per_page": 100}
    marked: list[dict[str, Any]] = []

    with httpx.Client() as client:
        resp = client.get(url, headers=_headers(), params=params)
        resp.raise_for_status()
        issues = [
            i
            for i in resp.json()
            if "pull_request" not in i
            and i.get("title", "").startswith("[ACADEMY")
        ]
        issues.sort(key=_academy_issue_order)

        for issue in issues:
            if level is not None:
                label_lv = f"level-{level}"
                if label_lv not in {l["name"] for l in issue.get("labels", [])}:
                    continue
            labels = {l["name"] for l in issue.get("labels", [])}
            if "agent-ready" in labels or "in-pipeline" in labels or "agent-done" in labels:
                continue

            num = issue["number"]
            client.post(
                f"{GITHUB_API}/repos/{target.github_repo}/issues/{num}/labels",
                headers=_headers(),
                json={"labels": ["agent-ready"]},
            )
            marked.append({"number": num, "title": issue["title"]})
            if len(marked) >= count:
                break

    return {"marked_count": len(marked), "marked": marked}


def run_academy_sprint(
    *,
    level: int | None = None,
    seed_if_missing: bool = True,
    mark_ready_count: int = 3,
) -> dict[str, Any]:
    """Orchestration: ensure issues exist, mark next N as agent-ready."""
    from services.academy_progress import load_progress, save_progress

    result: dict[str, Any] = {"workflow": "academy_sprint", "success": True}

    if level is not None and seed_if_missing:
        seed_result = seed_level(level, dry_run=False, mark_first_ready=False)
        result["seed"] = seed_result

    ready = mark_next_agent_ready(level=level, count=mark_ready_count)
    result["agent_ready"] = ready

    progress = load_progress()
    progress["last_sprint_at"] = datetime.now(timezone.utc).isoformat()
    if level:
        progress["current_level"] = level
    save_progress(progress)

    result["current_level"] = progress.get("current_level")
    return result
