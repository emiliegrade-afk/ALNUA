"""Auto-split from api/main.py — pipeline routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()


_pipeline_tasks: dict[str, dict[str, Any]] = {}


async def run_pipeline_background(
    task_id: str,
    issue_number: int,
    repo: str | None,
) -> None:
    """Runs the coding pipeline (skill_coding_agent) independently of HTTP."""
    from skills.skill_gh_issues import get_issue, process_issue

    task = _pipeline_tasks[task_id]
    pipeline_input = f"issue #{issue_number} on {repo or 'default'}"

    def _log(message: str) -> None:
        task["log"].append(message)

    with agent_trace("pipeline", input=pipeline_input) as trace:
        try:
            task["status"] = "running"
            task["progress"] = 10

            issue = await asyncio.to_thread(get_issue, issue_number, repo_slug=repo)
            task["progress"] = 25
            issue_title = issue.get("title", "")
            _log(f"Issue #{issue_number}: {issue_title}")

            repo_path = issue.get("_repo_path")
            if not repo_path:
                raise ValueError(
                    f"Issue #{issue_number} sans métadonnée repo — préciser ?repo=hub|academy|nomad|naia"
                )

            task["progress"] = 40
            _log("Lancement coding_agent (worktree + PR)...")

            result = await asyncio.to_thread(process_issue, issue, repo_path, None)

            if result.get("success"):
                task["status"] = "completed"
                task["progress"] = 100
                pr_url = result.get("pr_url") or ""
                _log(f"[OK] PR créée : {pr_url[:120]}")
                if trace:
                    trace.update(output="completed")
            else:
                task["status"] = "failed"
                task["progress"] = 100
                err = result.get("error") or "unknown"
                _log(f"[ERREUR] {err}")
                if trace:
                    trace.update(output=f"failed: {err}", level="ERROR")
        except Exception as exc:
            task["status"] = "failed"
            task["progress"] = 100
            _log(f"[ERREUR] Exception: {exc}")
            if trace:
                trace.update(output=f"failed: {exc}", level="ERROR")
            logger.exception("Pipeline task %s failed", task_id)


@router.get("/pipeline/issues")
async def get_ready_issues():
    """Liste les issues GitHub prêtes à être traitées."""
    try:
        return list_ready_issues()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/pipeline/run/{issue_number}")
async def run_pipeline(issue_number: int, repo: str | None = None):
    """Déclenche le pipeline sur une issue spécifique (repo=hub|naia|nomad)."""
    task_id = str(uuid.uuid4())
    _pipeline_tasks[task_id] = {
        "status": "starting",
        "log": [f"Pipeline queued for issue #{issue_number}"],
        "progress": 0,
        "issue_number": issue_number,
        "repo": repo,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    asyncio.create_task(run_pipeline_background(task_id, issue_number, repo))
    return {
        "status": "started",
        "task_id": task_id,
        "issue": issue_number,
        "repo": repo,
    }


@router.get("/pipeline/status/{task_id}")
async def pipeline_status(task_id: str):
    """Retourne l'état d'une exécution pipeline (polling côté client)."""
    task = _pipeline_tasks.get(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return {
        "status": task["status"],
        "log": task["log"],
        "progress": task["progress"],
    }


from services.agent_pipeline_registry import (
    ALL_BUREAU_AGENT_IDS,
    LOG_NAME_TO_AGENT_ID,
    OPENROOM_DISPLAY,
)

_OPENROOM_AGENT_IDS = ALL_BUREAU_AGENT_IDS
_LOG_NAME_TO_OPENROOM = LOG_NAME_TO_AGENT_ID
# Legacy log aliases (anciens IDs OpenRoom)
_LOG_NAME_TO_OPENROOM.update({
    "game_dir": "game_director",
    "dev_game": "dev_gaming",
})
_OPENROOM_DISPLAY = OPENROOM_DISPLAY


def _openroom_idle_agents() -> dict[str, dict[str, Any]]:
    return {
        agent_id: {
            "status": "idle",
            "currentTask": None,
            "currentFile": None,
            "recentCode": [],
            "log": [],
            "progress": None,
        }
        for agent_id in _OPENROOM_AGENT_IDS
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


def _set_openroom_status(
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


def _apply_task_details(
    agents: dict[str, dict[str, Any]],
    agent_id: str,
    task: dict[str, Any],
) -> None:
    if agent_id not in agents:
        return
    task_logs = [str(line) for line in task.get("log", [])]
    current_file, recent_code = extract_file_mentions(task_logs)
    agents[agent_id]["currentFile"] = current_file
    agents[agent_id]["recentCode"] = recent_code
    agents[agent_id]["log"] = task_logs
    agents[agent_id]["progress"] = task.get("progress", 0)


def _format_log_time(value: str | None) -> str:
    if not value:
        return "--:--"
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone(timezone.utc).strftime("%H:%M")
    except ValueError:
        return value[-8:-3] if len(value) >= 8 else "--:--"


@router.get("/agents/pipeline/audit")
async def agents_pipeline_audit() -> dict[str, Any]:
    """Audit connectivité pipeline — import + méthodes exécutables par agent."""
    from services.agent_pipeline_registry import audit_pipeline

    return audit_pipeline()


@router.get("/agents/status")
async def agents_status() -> dict[str, Any]:
    """Statut OpenRoom — agents + 20 derniers logs."""
    agents = _openroom_idle_agents()
    recent_logs: list[dict[str, str]] = []

    active_tasks = [
        task
        for task in _pipeline_tasks.values()
        if task.get("status") in {"starting", "running"}
    ]
    pipeline_active = len(active_tasks) > 0

    for task in active_tasks:
        last_log = task.get("log", [""])[-1]
        issue = task.get("issue_number")
        _set_openroom_status(agents, "dev_app", "working", last_log or None)
        _apply_task_details(agents, "dev_app", task)
        _set_openroom_status(
            agents,
            "pm",
            "waiting",
            f"Issue #{issue} en cours" if issue else "Pipeline en cours",
        )
        _apply_task_details(agents, "pm", task)
        started_at = task.get("started_at")
        for line in task.get("log", [])[-4:]:
            recent_logs.append(
                {
                    "time": _format_log_time(started_at),
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
                "time": _format_log_time(created_at),
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
            _set_openroom_status(agents, agent_id, "working", task_summary or None)
        elif log_status == "error":
            _set_openroom_status(agents, agent_id, "error", task_summary or None)
        elif log_status == "success":
            # Activité récente (< 3 min) : afficher la tâche même après succès
            recent_cutoff = datetime.now(timezone.utc) - timedelta(minutes=3)
            if created_dt >= recent_cutoff and task_summary:
                _set_openroom_status(agents, agent_id, "waiting", task_summary)

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

    return {
        "agents": agents,
        "recentLogs": recent_logs,
        "pipelineActive": pipeline_active,
    }


@router.get("/costs/today")
async def costs_today():
    try:
        return get_daily_costs()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/costs/month")
async def costs_month():
    try:
        return get_monthly_costs()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/costs/week")
async def costs_week():
    try:
        return get_weekly_costs()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


