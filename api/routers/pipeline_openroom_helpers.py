"""OpenRoom pipeline — agent status helpers."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from services.agent_pipeline_registry import ALL_BUREAU_AGENT_IDS

OPENROOM_AGENT_IDS = ALL_BUREAU_AGENT_IDS


def openroom_idle_agents() -> dict[str, dict[str, Any]]:
    return {
        agent_id: {
            "status": "idle",
            "currentTask": None,
            "currentFile": None,
            "recentCode": [],
            "log": [],
            "progress": None,
            "runId": None,
            "taskId": None,
            "recipeId": None,
            "missionId": None,
        }
        for agent_id in OPENROOM_AGENT_IDS
    }


def apply_workflow_runs_to_agents(agents: dict[str, dict[str, Any]]) -> None:
    """Overlay recent workflow_runs onto OpenRoom — real run/task IDs (DEC-021)."""
    try:
        from services.workflow_engine_store import list_runs, get_run
    except Exception:
        return

    active_statuses = {"running", "blocked", "pending"}
    for summary in list_runs(limit=25):
        status = str(summary.get("status") or "")
        run_id = str(summary.get("run_id") or "")
        recipe_id = str(summary.get("recipe_id") or "")
        if not run_id:
            continue
        run = get_run(run_id)
        if not run:
            continue
        head = None
        try:
            from services.workflow_engine_catalog import get_recipe

            recipe = get_recipe(recipe_id)
            head = recipe.head_agent if recipe else None
        except Exception:
            head = None
        # Normalize *_agent → persona id when needed
        agent_id = (head or "").replace("_agent", "") if head else ""
        if agent_id not in agents:
            # idle drain may tag agents in context
            ctx_agents = list((run.context or {}).get("_idle_agent_ids") or [])
            agent_id = str(ctx_agents[0]) if ctx_agents else ""
        if agent_id not in agents:
            continue

        task_label = summary.get("summary") or recipe_id or run_id
        if status in active_statuses or status == "in_progress":
            set_openroom_status(agents, agent_id, "working", str(task_label)[:160])
            agents[agent_id]["runId"] = run_id
            agents[agent_id]["recipeId"] = recipe_id
            agents[agent_id]["taskId"] = run_id
            # Rough progress from finished steps
            steps = run.steps or []
            if steps:
                done = sum(1 for s in steps if str(s.status) in {"OK", "A_VERIFIER"})
                agents[agent_id]["progress"] = int(100 * done / max(len(steps), 1))
        elif status == "completed":
            # Recently finished — waiting with run id, no fake load
            if not agents[agent_id].get("runId"):
                set_openroom_status(agents, agent_id, "waiting", str(task_label)[:160])
                agents[agent_id]["runId"] = run_id
                agents[agent_id]["recipeId"] = recipe_id
                agents[agent_id]["taskId"] = run_id
                agents[agent_id]["progress"] = 100


def apply_missions_to_agents(agents: dict[str, dict[str, Any]]) -> None:
    """Overlay active Mission Graph tasks onto OpenRoom (DEC-023)."""
    try:
        from services.mission_graph_store import get_mission, list_missions
    except Exception:
        return

    for summary in list_missions(limit=20):
        status = str(summary.get("status") or "")
        if status not in {"IN_PROGRESS", "BLOCKED", "A_VERIFIER"}:
            continue
        mid = str(summary.get("mission_id") or "")
        if not mid:
            continue
        mission = get_mission(mid)
        if not mission:
            continue
        progress = mission.progress_pct()
        for task in mission.tasks:
            aid = (task.agent_id or "").replace("_agent", "")
            if aid not in agents:
                continue
            label = f"{mission.title}: {task.description}"[:160]
            if task.status == "EXECUTING":
                set_openroom_status(agents, aid, "working", label)
                agents[aid]["runId"] = mid
                agents[aid]["taskId"] = task.task_id
                agents[aid]["missionId"] = mid
                agents[aid]["progress"] = progress
            elif task.status == "READY" and agents[aid].get("status") in {"idle", "waiting"}:
                set_openroom_status(agents, aid, "waiting", label)
                agents[aid]["runId"] = mid
                agents[aid]["taskId"] = task.task_id
                agents[aid]["missionId"] = mid
                agents[aid]["progress"] = progress
            elif task.status == "FAILED":
                set_openroom_status(agents, aid, "error", label)
                agents[aid]["runId"] = mid
                agents[aid]["taskId"] = task.task_id
                agents[aid]["missionId"] = mid


def extract_file_mentions(logs: list[str]) -> tuple[str | None, list[str]]:
    """Return (last mentioned file path, recent code-like log lines)."""
    current_file: str | None = None
    code_lines: list[str] = []
    for line in reversed(logs[-20:]):
        match = re.search(r"[\w/.-]+\.(tsx|ts|py|js|jsx)", line)
        if match and not current_file:
            current_file = match.group(0)
        stripped = line.strip()
        if stripped.startswith(
            (" ", "\t", "import", "export", "const", "def", "function", "//")
        ):
            code_lines.insert(0, stripped)
        if len(code_lines) >= 6:
            break
    return current_file, code_lines


def set_openroom_status(
    agents: dict[str, dict[str, Any]],
    agent_id: str,
    status: str,
    current_task: str | None = None,
) -> None:
    if agent_id not in agents:
        return
    priority = {"idle": 0, "waiting": 1, "working": 2, "error": 3}
    current = agents[agent_id]["status"] or "idle"
    if priority.get(status, 0) >= priority.get(current, 0):
        agents[agent_id]["status"] = status
        if current_task:
            agents[agent_id]["currentTask"] = current_task


def apply_task_details(
    agents: dict[str, dict[str, Any]],
    agent_id: str,
    task: dict[str, Any],
) -> None:
    if agent_id not in agents:
        return
    task_logs = [str(line) for line in task.get("log", [])]
    current_file = task.get("current_file")
    recent_code = task.get("recent_code") or []
    if not current_file or not recent_code:
        parsed_file, parsed_code = extract_file_mentions(task_logs)
        current_file = current_file or parsed_file
        recent_code = recent_code or parsed_code
    agents[agent_id]["currentFile"] = current_file
    agents[agent_id]["recentCode"] = recent_code
    agents[agent_id]["log"] = task_logs
    agents[agent_id]["progress"] = task.get("progress", 0)


def format_log_time(value: str | None) -> str:
    if not value:
        return "--:--"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%H:%M")
    except ValueError:
        return value[-8:-3] if len(value) >= 8 else "--:--"
