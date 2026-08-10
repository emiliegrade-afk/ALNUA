"""Pipeline task routes — issue run/status."""

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
                    f"Issue #{issue_number} sans métadonnée repo — préciser ?repo=hub|academy"
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
    """Déclenche le pipeline sur une issue spécifique (repo=hub|academy)."""
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
