"""Mission Graph dispatch — sequential/parallel via plan_executor steps (DEC-023)."""

from __future__ import annotations

import concurrent.futures
import logging
from typing import Any

from services.mission_graph_models import Mission, MissionTask, _now_iso
from services.mission_graph_store import get_mission, save_mission
from services.plan_executor_models import ExecutionStep

logger = logging.getLogger(__name__)


def _deps_satisfied(task: MissionTask, by_id: dict[str, MissionTask]) -> bool:
    if not task.depends_on:
        return True
    return all(
        by_id[d].status == "COMPLETED"
        for d in task.depends_on
        if d in by_id
    )


def _deps_failed(task: MissionTask, by_id: dict[str, MissionTask]) -> bool:
    for d in task.depends_on:
        dep = by_id.get(d)
        if dep is None:
            return True
        if dep.status in {"FAILED", "BLOCKED", "SKIPPED"}:
            return True
    return False


def refresh_ready_and_blocked(mission: Mission) -> None:
    by_id = mission.task_map()
    for task in mission.tasks:
        if task.status in {"COMPLETED", "FAILED", "SKIPPED", "A_VERIFIER", "EXECUTING"}:
            continue
        if _deps_failed(task, by_id):
            task.status = "BLOCKED"
            task.error = task.error or "Blocked by dependency failure"
        elif _deps_satisfied(task, by_id):
            if task.status in {"PENDING", "BLOCKED"}:
                task.status = "READY"
    mission.recompute_status()


def _to_execution_step(task: MissionTask) -> ExecutionStep:
    return ExecutionStep(
        step_id=task.task_id,
        description=task.description,
        agent_id=task.agent_id,
        method=task.method,
        kwargs=dict(task.kwargs or {}),
        depends_on=list(task.depends_on or []),
        lock_keys=list(task.lock_keys or []),
        repo_slug=task.repo_slug,
        repo_path=task.repo_path,
    )


def _apply_step_result(task: MissionTask, result: Any) -> None:
    from services.plan_executor_models import StepResult

    task.finished_at = _now_iso()
    if isinstance(result, StepResult):
        task.duration_ms = result.duration_ms
        task.retries = result.retries
        if result.success:
            task.status = "COMPLETED"
            task.result = result.result
            task.error = None
        else:
            task.status = "FAILED"
            task.error = result.error
            task.result = None
    else:
        task.status = "FAILED"
        task.error = "Invalid step result"


def run_mission(
    mission_id: str,
    *,
    max_concurrent: int = 4,
    stop_on_failure: bool = False,
    max_retries: int = 2,
) -> dict[str, Any]:
    """Execute a persisted Mission Graph (batches of READY tasks)."""
    from services.plan_executor_run import _execute_step

    mission = get_mission(mission_id)
    if not mission:
        return {"error": f"Mission not found: {mission_id}", "mission_id": mission_id}
    if not mission.tasks:
        return {"error": "Mission has no tasks", "mission_id": mission_id}

    if mission.started_at is None:
        mission.started_at = _now_iso()
    mission.status = "IN_PROGRESS"
    save_mission(mission)

    try:
        from services.event_bus import emit

        emit(
            "mission.started",
            {"mission_id": mission.mission_id, "title": mission.title},
            source_agent="mission_graph",
        )
    except Exception:
        pass

    while True:
        refresh_ready_and_blocked(mission)
        save_mission(mission)

        ready = [t for t in mission.tasks if t.status == "READY"]
        if not ready:
            break

        batch = ready[: max(1, max_concurrent)]
        for t in batch:
            t.status = "EXECUTING"
            t.started_at = _now_iso()
            t.error = None
        save_mission(mission)

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(batch)) as pool:
            futures = {
                pool.submit(_execute_step, _to_execution_step(t), max_retries): t
                for t in batch
            }
            for fut in concurrent.futures.as_completed(futures):
                task = futures[fut]
                try:
                    step_result = fut.result()
                except Exception as exc:
                    task.status = "FAILED"
                    task.error = str(exc)
                    task.finished_at = _now_iso()
                    step_result = None
                if step_result is not None:
                    _apply_step_result(task, step_result)
                try:
                    from services.event_bus import emit

                    emit(
                        "mission.task_finished",
                        {
                            "mission_id": mission.mission_id,
                            "task_id": task.task_id,
                            "agent_id": task.agent_id,
                            "status": task.status,
                        },
                        source_agent=task.agent_id,
                    )
                except Exception:
                    pass
                save_mission(mission)

                if stop_on_failure and task.status == "FAILED":
                    # Mark remaining pending as blocked and exit
                    for other in mission.tasks:
                        if other.status in {"PENDING", "READY"}:
                            other.status = "BLOCKED"
                            other.error = f"Stopped after failure of {task.task_id}"
                    break

        if stop_on_failure and any(t.status == "FAILED" for t in batch):
            break

    refresh_ready_and_blocked(mission)
    status = mission.recompute_status()
    if status in {"COMPLETED", "FAILED", "BLOCKED", "A_VERIFIER"}:
        mission.finished_at = _now_iso()
    save_mission(mission)

    try:
        from services.event_bus import emit

        emit(
            "mission.completed",
            {
                "mission_id": mission.mission_id,
                "status": mission.status,
                "progress_pct": mission.progress_pct(),
            },
            source_agent="mission_graph",
        )
    except Exception:
        pass

    return {
        "mission_id": mission.mission_id,
        "title": mission.title,
        "status": mission.status,
        "progress_pct": mission.progress_pct(),
        "graph": mission.graph_summary(),
        "tasks": [t.to_dict() for t in mission.tasks],
        "finished_at": mission.finished_at,
    }


def create_and_run_from_objective(
    objective: str,
    context: str = "",
    *,
    max_concurrent: int = 4,
    stop_on_failure: bool = False,
) -> dict[str, Any]:
    from services.mission_graph_build import mission_from_objective

    mission = mission_from_objective(objective, context, persist=True)
    result = run_mission(
        mission.mission_id,
        max_concurrent=max_concurrent,
        stop_on_failure=stop_on_failure,
    )
    return {"mission": get_mission(mission.mission_id).to_dict() if get_mission(mission.mission_id) else None, **result}


def abort_mission(
    mission_id: str,
    *,
    agent_id: str,
    reason: str = "",
) -> dict[str, Any]:
    """Cancel an in-flight mission — gated by workflow:abort."""
    from services.mission_graph_models import _now_iso
    from services.permission_guard import PermissionDeniedError, require_capability

    try:
        require_capability(
            agent_id,
            "workflow:abort",
            resource=f"mission:{mission_id}",
            meta={"reason": (reason or "")[:120]},
        )
    except PermissionDeniedError as exc:
        return {"ok": False, "error": "capability_denied", "detail": str(exc)}

    mission = get_mission(mission_id)
    if not mission:
        return {"ok": False, "error": "not_found"}
    if mission.status in {"COMPLETED", "CANCELLED"}:
        return {
            "ok": False,
            "error": "already_terminal",
            "status": mission.status,
            "mission_id": mission_id,
        }

    note = (reason or "aborted").strip()[:200]
    for task in mission.tasks:
        if task.status in {"PENDING", "READY", "EXECUTING", "BLOCKED"}:
            task.status = "SKIPPED"
            task.error = f"aborted by {agent_id}: {note}"[:300]

    mission.status = "CANCELLED"
    mission.finished_at = _now_iso()
    save_mission(mission)
    return {
        "ok": True,
        "mission_id": mission_id,
        "status": "CANCELLED",
        "aborted_by": agent_id,
    }
