"""Academy queue helpers for agent wake — split from agent_wake (Vague 5)."""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

from config.github_repos import get_target_by_slug

logger = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"


def _headers() -> dict[str, str]:
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise ValueError("GITHUB_TOKEN manquant")
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _academy_open_issues() -> list[dict[str, Any]]:
    from services.academy_progress import fetch_academy_github_issues

    return [i for i in fetch_academy_github_issues() if i.get("state") == "open"]


def academy_label_counts() -> dict[str, int]:
    """Live counts from GitHub (open academy exercises only)."""
    counts = {"agent-ready": 0, "in-pipeline": 0, "agent-failed": 0}
    for issue in _academy_open_issues():
        if "pull_request" in issue:
            continue
        labels = {lbl.get("name", "") for lbl in issue.get("labels", [])}
        for key in counts:
            if key in labels:
                counts[key] += 1
    return counts


def _pipeline_slots_free() -> tuple[int, int]:
    """Return (free_slots, max_parallel)."""
    from services.coding_pipeline import get_coding_config

    cfg = get_coding_config()
    counts = academy_label_counts()
    busy = counts["agent-ready"] + counts["in-pipeline"]
    return max(0, cfg.max_parallel - busy), cfg.max_parallel


def queue_academy_if_idle(*, count: int | None = None) -> dict[str, Any]:
    """
    Label next open Academy issues agent-ready when pipeline has free slots.
    Safe to call after every merge or on an idle poll tick.
    """
    target = get_target_by_slug("academy")
    if not target:
        return {"marked_count": 0, "reason": "academy_not_configured", "marked": []}

    slots, max_parallel = _pipeline_slots_free()
    if slots <= 0:
        counts = academy_label_counts()
        return {
            "marked_count": 0,
            "reason": "pipeline_full",
            "slots_free": 0,
            "max_parallel": max_parallel,
            **counts,
            "marked": [],
        }

    from services.academy_progress import load_progress, save_progress
    from services.academy_seed import mark_next_agent_ready

    try:
        from services.academy_progress import fetch_academy_github_issues, sync_from_github_issues

        sync_from_github_issues(fetch_academy_github_issues())
    except Exception as exc:
        logger.warning("[AgentWake] progress sync skipped: %s", exc)

    progress = load_progress()
    current = int(progress.get("current_level") or 1)
    n = min(count if count is not None else slots, slots)
    result: dict[str, Any] = {"marked_count": 0, "marked": []}
    queued_level = current
    for lv in range(current, 5):
        result = mark_next_agent_ready(level=lv, count=n)
        if result.get("marked_count"):
            queued_level = lv
            break
    if result.get("marked_count") and queued_level != current:
        progress["current_level"] = queued_level
        save_progress(progress)
    elif not result.get("marked_count") and slots > 0:
        try:
            from services.academy_curriculum import LEVEL_META
            from services.academy_seed import seed_level

            seed_level_num: int | None = None
            levels = progress.get("levels") or {}
            for lv in range(1, 5):
                key = str(lv)
                meta = levels.get(key, {})
                total = int(meta.get("total") or LEVEL_META[lv]["issues"])
                done = int(meta.get("done") or 0)
                failed = int(meta.get("failed") or 0)
                if done + failed < total or (done < total and lv >= current):
                    seed_level_num = lv
                    break
            if seed_level_num is not None:
                seeded = seed_level(level=seed_level_num, dry_run=False, mark_first_ready=False)
                if seeded.get("created_count"):
                    result["seed"] = seeded
                    for lv in range(seed_level_num, 5):
                        result = mark_next_agent_ready(level=lv, count=n)
                        if result.get("marked_count"):
                            queued_level = lv
                            progress["current_level"] = lv
                            save_progress(progress)
                            break
        except Exception as exc:
            logger.warning("[AgentWake] auto-seed skipped: %s", exc)

    result["reason"] = "queued" if result.get("marked_count") else "nothing_to_queue"
    if result.get("marked_count"):
        result["queued_level"] = queued_level
    result["slots_free"] = slots
    result["max_parallel"] = max_parallel
    return result


def requeue_failed_academy(*, count: int = 1) -> dict[str, Any]:
    """Relabel agent-failed → agent-ready so dev_app retries."""
    target = get_target_by_slug("academy")
    if not target or count <= 0:
        return {"retried_count": 0, "retried": []}

    retried: list[dict[str, Any]] = []
    url = f"{GITHUB_API}/repos/{target.github_repo}/issues"
    params = {"state": "open", "per_page": 100, "labels": "agent-failed"}

    with httpx.Client() as client:
        resp = client.get(url, headers=_headers(), params=params)
        resp.raise_for_status()
        issues = [
            i
            for i in resp.json()
            if "pull_request" not in i and i.get("title", "").startswith("[ACADEMY")
        ]
        issues.sort(key=lambda i: i.get("number", 0))

        for issue in issues[:count]:
            num = issue["number"]
            labels = [l["name"] for l in issue.get("labels", []) if l["name"] != "agent-failed"]
            if "agent-ready" not in labels:
                labels.append("agent-ready")
            client.patch(
                f"{GITHUB_API}/repos/{target.github_repo}/issues/{num}",
                headers=_headers(),
                json={"labels": labels},
            )
            retried.append({"number": num, "title": issue.get("title", "")})

    return {"retried_count": len(retried), "retried": retried}
