"""In-memory coding task registry — visible in /agents/status (poll + manual runs)."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_ROOT = Path(__file__).resolve().parents[1]
_PIPELINE_LOG = _ROOT / "data" / "coding_pipeline.log"

_tasks: dict[str, dict[str, Any]] = {}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _append_file_log(message: str) -> None:
    """CEO-visible trail — tail data/coding_pipeline.log."""
    try:
        _PIPELINE_LOG.parent.mkdir(parents=True, exist_ok=True)
        line = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} {message}"
        with _PIPELINE_LOG.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception as exc:
        logger.debug("[CodingActivity] log file skip: %s", exc)


def github_academy_in_pipeline() -> list[dict[str, Any]]:
    """Live GitHub labels — survives Hub restarts."""
    try:
        from services.academy_progress import fetch_academy_github_issues

        out: list[dict[str, Any]] = []
        for issue in fetch_academy_github_issues():
            if "pull_request" in issue:
                continue
            labels = {lbl.get("name", "") for lbl in issue.get("labels", [])}
            if "in-pipeline" not in labels:
                continue
            out.append(
                {
                    "issue_number": issue.get("number"),
                    "title": issue.get("title", ""),
                    "repo_slug": "academy",
                }
            )
        return out
    except Exception as exc:
        logger.debug("[CodingActivity] github in-pipeline: %s", exc)
        return []


def start_task(
    *,
    issue_number: int,
    title: str,
    repo_slug: str,
    github_repo: str,
    worktree_path: str | None = None,
    agent_id: str = "dev_app",
) -> str:
    task_id = f"gh-{repo_slug}-{issue_number}"
    _tasks[task_id] = {
        "task_id": task_id,
        "status": "running",
        "issue_number": issue_number,
        "title": title,
        "repo_slug": repo_slug,
        "github_repo": github_repo,
        "worktree_path": worktree_path,
        "agent_id": agent_id,
        "current_file": None,
        "recent_code": [],
        "progress": 5,
        "log": [f"Issue #{issue_number}: {title}"],
        "started_at": _now(),
        "ended_at": None,
    }
    _append_file_log(
        f"[START] #{issue_number} ({repo_slug}) {title[:100]}"
    )
    return task_id


def set_worktree_path(task_id: str, worktree_path: str) -> None:
    task = _tasks.get(task_id)
    if task:
        task["worktree_path"] = worktree_path


def get_active_worktree_path() -> str | None:
    for task in _tasks.values():
        if task.get("status") in {"starting", "running"} and task.get("worktree_path"):
            return str(task["worktree_path"])
    return None


def record_agent_action(
    task_id: str,
    *,
    action: str,
    path: str | None = None,
    code_snippet: list[str] | None = None,
    progress: int | None = None,
) -> None:
    """Live trail for IDE + OpenRoom during hub_coding_agent turns."""
    task = _tasks.get(task_id)
    if not task:
        return
    label = action
    if path:
        label = f"{action} → {path}"
        task["current_file"] = path
    task["log"].append(label)
    if len(task["log"]) > 80:
        task["log"] = task["log"][-80:]
    if code_snippet:
        task["recent_code"] = code_snippet[-12:]
    if progress is not None:
        task["progress"] = max(0, min(100, progress))
    _append_file_log(f"[{task_id}] {label}")


def append_log(task_id: str, message: str) -> None:
    task = _tasks.get(task_id)
    if not task:
        return
    task["log"].append(message)
    if len(task["log"]) > 80:
        task["log"] = task["log"][-80:]


def set_progress(task_id: str, progress: int) -> None:
    task = _tasks.get(task_id)
    if task:
        task["progress"] = max(0, min(100, progress))


def finish_task(task_id: str, *, success: bool, message: str) -> None:
    task = _tasks.get(task_id)
    if not task:
        return
    task["status"] = "completed" if success else "failed"
    task["progress"] = 100
    task["ended_at"] = _now()
    append_log(task_id, message)
    tag = "OK" if success else "FAIL"
    num = task.get("issue_number", "?")
    _append_file_log(f"[{tag}] #{num} {message[:120]}")


def active_tasks() -> list[dict[str, Any]]:
    """Tasks still running (poll loop or /pipeline/run)."""
    return [t for t in _tasks.values() if t.get("status") in {"starting", "running"}]


def recent_tasks(*, limit: int = 10) -> list[dict[str, Any]]:
    """Recent tasks including just-finished (kept ~30 min for monitoring)."""
    from datetime import timedelta

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
    out: list[dict[str, Any]] = []
    for task in sorted(
        _tasks.values(),
        key=lambda t: t.get("ended_at") or t.get("started_at") or "",
        reverse=True,
    ):
        ended = task.get("ended_at") or task.get("started_at")
        if ended:
            try:
                dt = datetime.fromisoformat(str(ended).replace("Z", "+00:00"))
                if dt < cutoff and task.get("status") not in {"starting", "running"}:
                    continue
            except ValueError:
                pass
        out.append(task)
        if len(out) >= limit:
            break
    return out
