"""ALNUA Academy progress tracking — manifest JSON + GitHub sync."""

from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_PROGRESS_PATH = Path(
    os.getenv("ACADEMY_PROGRESS_PATH", str(_PROJECT_ROOT / "data" / "academy_progress.json"))
)

_ACADEMY_TITLE_RE = re.compile(r"^\[ACADEMY\s+(N\d+\.\d+)\]", re.I)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_progress() -> dict[str, Any]:
    from services.academy_curriculum import LEVEL_META, all_exercises

    total = len(all_exercises())
    levels = {
        str(lv): {
            "name": meta["name"],
            "total": meta["issues"],
            "done": 0,
            "failed": 0,
            "in_progress": 0,
        }
        for lv, meta in LEVEL_META.items()
    }
    return {
        "version": 1,
        "updated_at": _now_iso(),
        "current_level": 1,
        "total_exercises": total,
        "completed_exercises": 0,
        "failed_exercises": 0,
        "success_rate_pct": 0.0,
        "levels": levels,
        "gate_nuaway": {
            "academy_n4_stable": False,
            "success_rate_65": False,
            "mem0_lessons_35": False,
            "error_journal_top5": False,
            "lounge_product_ready": False,
        },
        "last_sprint_at": None,
        "notes": "ALNUA Academy — entraînement dev_app avant produit Lounge",
    }


def load_progress() -> dict[str, Any]:
    if not _PROGRESS_PATH.is_file():
        data = default_progress()
        save_progress(data)
        return data
    try:
        return json.loads(_PROGRESS_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("academy progress read failed: %s", exc)
        return default_progress()


def save_progress(data: dict[str, Any]) -> Path:
    _PROGRESS_PATH.parent.mkdir(parents=True, exist_ok=True)
    data["updated_at"] = _now_iso()
    _PROGRESS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return _PROGRESS_PATH


def _level_from_exercise_id(exercise_id: str) -> int:
    m = re.match(r"N(\d+)", exercise_id, re.I)
    return int(m.group(1)) if m else 0


def sync_from_github_issues(issues: list[dict[str, Any]]) -> dict[str, Any]:
    """Recompute progress from GitHub issues (titles [ACADEMY Nx.y])."""
    from services.academy_curriculum import LEVEL_META

    progress = load_progress()
    levels = {
        str(lv): {
            "name": LEVEL_META[lv]["name"],
            "total": LEVEL_META[lv]["issues"],
            "done": 0,
            "failed": 0,
            "in_progress": 0,
        }
        for lv in LEVEL_META
    }

    done_ids: set[str] = set()
    failed_ids: set[str] = set()
    in_progress_ids: set[str] = set()

    for issue in issues:
        title = issue.get("title") or ""
        m = _ACADEMY_TITLE_RE.match(title)
        if not m:
            continue
        eid = m.group(1).upper()
        lv = str(_level_from_exercise_id(eid))
        labels = {lbl.get("name", "") for lbl in issue.get("labels", [])}
        state = issue.get("state", "open")

        if "agent-failed" in labels:
            failed_ids.add(eid)
            if lv in levels:
                levels[lv]["failed"] += 1
        elif state == "closed" or "agent-done" in labels:
            done_ids.add(eid)
            if lv in levels:
                levels[lv]["done"] += 1
        elif "in-pipeline" in labels or "agent-ready" in labels:
            in_progress_ids.add(eid)
            if lv in levels:
                levels[lv]["in_progress"] += 1

    completed = len(done_ids)
    failed = len(failed_ids)
    attempted = completed + failed
    success_rate = round(100.0 * completed / attempted, 1) if attempted else 0.0

    # Current level = first level not fully done
    current_level = 4
    for lv in (1, 2, 3, 4):
        key = str(lv)
        if levels[key]["done"] < levels[key]["total"]:
            current_level = lv
            break

    progress["levels"] = levels
    progress["current_level"] = current_level
    progress["completed_exercises"] = completed
    progress["failed_exercises"] = failed
    progress["success_rate_pct"] = success_rate
    progress["gate_nuaway"]["success_rate_65"] = success_rate >= 65.0
    progress["gate_nuaway"]["academy_n4_stable"] = (
        levels["4"]["done"] >= levels["4"]["total"] and failed == 0
    )
    try:
        from services.coding_error_journal import count_resolved

        progress["gate_nuaway"]["error_journal_top5"] = count_resolved() >= 5
    except Exception:
        pass

    save_progress(progress)
    return progress


def fetch_academy_github_issues() -> list[dict[str, Any]]:
    """Open issues on academy repo matching [ACADEMY prefix."""
    import httpx

    from config.github_repos import get_target_by_slug

    token = os.getenv("GITHUB_TOKEN", "").strip()
    target = get_target_by_slug("academy")
    if not token or not target:
        return []

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    url = f"https://api.github.com/repos/{target.github_repo}/issues"
    params = {"state": "all", "per_page": 100, "labels": ""}

    with httpx.Client() as client:
        resp = client.get(url, headers=headers, params=params)
        resp.raise_for_status()
        issues = resp.json()

    return [
        i
        for i in issues
        if _ACADEMY_TITLE_RE.match(i.get("title") or "")
        and "pull_request" not in i
    ]


def get_academy_status() -> dict[str, Any]:
    """Full status for cockpit API."""
    from services.academy_curriculum import LEVEL_META, all_exercises

    issues: list[dict[str, Any]] = []
    github_error: str | None = None
    try:
        issues = fetch_academy_github_issues()
    except Exception as exc:
        github_error = str(exc)[:200]

    progress = sync_from_github_issues(issues) if issues else load_progress()

    mem0_snippet = ""
    try:
        from skills.skill_mem0 import recall

        mem0_snippet = (recall(query="dev_app academy lessons", agent_id="dev_app") or "")[:800]
    except Exception:
        pass

    progress["gate_nuaway"]["mem0_lessons_35"] = len(mem0_snippet) > 200

    target_configured = bool(os.getenv("GITHUB_REPO_ACADEMY", "").strip())
    local_path = os.getenv("REPO_PATH_ACADEMY", "")
    path_exists = Path(local_path).is_dir() if local_path else False

    return {
        "progress": progress,
        "curriculum_total": len(all_exercises()),
        "level_meta": LEVEL_META,
        "github_issues_count": len(issues),
        "github_error": github_error,
        "repo_configured": target_configured,
        "repo_path_exists": path_exists,
        "mem0_snippet": mem0_snippet,
        "progress_file": str(_PROGRESS_PATH),
    }
