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
        }
        for agent_id in OPENROOM_AGENT_IDS
    }


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
