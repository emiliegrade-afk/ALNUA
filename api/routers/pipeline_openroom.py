"""Pipeline OpenRoom agent status routes."""

from __future__ import annotations

import time

from api.route_common import *  # noqa: F403
from api.routers.pipeline_openroom_helpers import (
    apply_task_details,
    extract_file_mentions,
    format_log_time,
    openroom_idle_agents,
    set_openroom_status,
)
from api.routers.pipeline_tasks import _pipeline_tasks

router = APIRouter()

_agents_status_cache: tuple[float, dict[str, Any]] | None = None
_AGENTS_STATUS_TTL_S = 3.0

from services.agent_pipeline_registry import (
    LOG_NAME_TO_AGENT_ID,
    OPENROOM_DISPLAY,
)

_LOG_NAME_TO_OPENROOM = LOG_NAME_TO_AGENT_ID
_LOG_NAME_TO_OPENROOM.update({
    "game_dir": "game_director",
    "dev_game": "dev_gaming",
})
_OPENROOM_DISPLAY = OPENROOM_DISPLAY


@router.get("/agents/pipeline/audit")
async def agents_pipeline_audit() -> dict[str, Any]:
    """Audit connectivité pipeline — import + méthodes exécutables par agent."""
    from services.agent_pipeline_registry import audit_pipeline

    return audit_pipeline()


@router.get("/agents/status")
async def agents_status() -> dict[str, Any]:
    """Statut OpenRoom — agents + 20 derniers logs."""
    global _agents_status_cache

    def _pipeline_busy() -> bool:
        if any(
            t.get("status") in {"starting", "running"}
            for t in _pipeline_tasks.values()
        ):
            return True
        try:
            from services.coding_activity import active_tasks as poll_active_tasks

            return bool(poll_active_tasks())
        except Exception:
            return False

    busy = _pipeline_busy()
    now = time.monotonic()
    if (
        not busy
        and _agents_status_cache is not None
        and now - _agents_status_cache[0] < _AGENTS_STATUS_TTL_S
    ):
        return _agents_status_cache[1]

    agents = openroom_idle_agents()
    recent_logs: list[dict[str, str]] = []
    pipeline_active = False

    active_tasks = [
        task
        for task in _pipeline_tasks.values()
        if task.get("status") in {"starting", "running"}
    ]
    try:
        from services.coding_activity import active_tasks as poll_active_tasks

        for pt in poll_active_tasks():
            active_tasks.append(
                {
                    "status": "running",
                    "log": pt.get("log", []),
                    "progress": pt.get("progress", 0),
                    "issue_number": pt.get("issue_number"),
                    "started_at": pt.get("started_at"),
                    "repo": pt.get("repo_slug"),
                    "current_file": pt.get("current_file"),
                    "recent_code": pt.get("recent_code", []),
                }
            )
    except Exception:
        pass

    try:
        from services.coding_activity import github_academy_in_pipeline

        for gh in github_academy_in_pipeline():
            num = gh.get("issue_number")
            title = str(gh.get("title", ""))[:80]
            msg = f"Academy #{num}: {title}"
            if agents["dev_app"]["status"] == "idle":
                set_openroom_status(agents, "dev_app", "working", msg)
            recent_logs.insert(
                0,
                {
                    "time": format_log_time(datetime.now(timezone.utc).isoformat()),
                    "agent": "DEV",
                    "message": msg,
                },
            )
            pipeline_active = True
    except Exception:
        pass

    pipeline_active = pipeline_active or len(active_tasks) > 0

    for task in active_tasks:
        last_log = task.get("log", [""])[-1]
        issue = task.get("issue_number")
        set_openroom_status(agents, "dev_app", "working", last_log or None)
        apply_task_details(agents, "dev_app", task)
        set_openroom_status(
            agents,
            "pm",
            "waiting",
            f"Issue #{issue} en cours" if issue else "Pipeline en cours",
        )
        apply_task_details(agents, "pm", task)
        started_at = task.get("started_at")
        for line in task.get("log", [])[-4:]:
            recent_logs.append(
                {
                    "time": format_log_time(started_at),
                    "agent": "DEV",
                    "message": line,
                }
            )

    try:
        db = get_supabase()
        db_logs = db.select(
            "agent_logs",
            order_by="created_at",
            ascending=False,
            limit=20,
        )
    except Exception:
        db_logs = []

    cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
    for entry in db_logs:
        raw_name = str(entry.get("agent_name", ""))
        agent_id = _LOG_NAME_TO_OPENROOM.get(raw_name)
        display = _OPENROOM_DISPLAY.get(agent_id or "", raw_name[:8].upper())
        action = str(entry.get("action", ""))
        output = str(entry.get("output_summary", "") or entry.get("input_summary", ""))
        message = output or action
        created_at = str(entry.get("created_at", ""))
        recent_logs.append(
            {
                "time": format_log_time(created_at),
                "agent": display,
                "message": message,
            }
        )

        if not agent_id:
            continue

        try:
            created_dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
        except ValueError:
            continue
        if created_dt < cutoff:
            continue

        log_status = str(entry.get("status", "success"))
        task_summary = output or action
        if log_status == "pending":
            set_openroom_status(agents, agent_id, "working", task_summary or None)
        elif log_status == "error":
            set_openroom_status(agents, agent_id, "error", task_summary or None)
        elif log_status == "success":
            recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=3)
            if created_dt >= recent_cutoff and task_summary:
                set_openroom_status(agents, agent_id, "waiting", task_summary)

        agent_log_lines = agents[agent_id].setdefault("log", [])
        if message and message not in agent_log_lines:
            agent_log_lines.append(message)
        agents[agent_id]["log"] = agent_log_lines[-20:]
        current_file, recent_code = extract_file_mentions(agents[agent_id]["log"])
        if current_file:
            agents[agent_id]["currentFile"] = current_file
        if recent_code:
            agents[agent_id]["recentCode"] = recent_code

    recent_logs = recent_logs[:20]

    try:
        from services.coding_activity import github_academy_in_pipeline
        from services.agent_wake import academy_label_counts

        gh_counts = academy_label_counts()
    except Exception:
        gh_counts = {}
        github_academy_in_pipeline = lambda: []  # type: ignore[assignment,misc]

    result = {
        "agents": agents,
        "recentLogs": recent_logs,
        "pipelineActive": pipeline_active,
        "codingPipeline": {
            "activeTasks": len(active_tasks),
            "githubInPipeline": gh_counts.get("in-pipeline", 0),
            "githubAgentReady": gh_counts.get("agent-ready", 0),
            "githubFailed": gh_counts.get("agent-failed", 0),
            "inPipelineIssues": github_academy_in_pipeline(),
        },
    }
    if not busy:
        _agents_status_cache = (time.monotonic(), result)
    return result
