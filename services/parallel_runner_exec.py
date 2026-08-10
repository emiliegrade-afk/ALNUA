"""Parallel runner — async/sync execution with retry and dependencies."""

from __future__ import annotations

import asyncio
import inspect
import time
import uuid
from typing import Any

from services.parallel_runner_progress import _TASK_PROGRESS
from services.parallel_runner_types import AgentResult, AgentTask, _get_agent_method


async def _run_single_task(
    task: AgentTask,
    run_id: str = "",
    progress: dict[str, Any] | None = None,
) -> AgentResult:
    """Exécute une seule tâche agent avec retry automatique (backoff exponentiel)."""
    start = time.monotonic()
    label = task.label
    max_retries = min(task.max_retries, 3)
    retries = 0
    last_error = ""

    if progress is not None:
        progress[label] = {"status": "running", "retries": 0, "started_at": time.time()}

    while True:
        try:
            method = _get_agent_method(task.agent_id, task.method)
            if inspect.iscoroutinefunction(method):
                result = await method(**task.kwargs)
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: method(**task.kwargs))
            duration_ms = int((time.monotonic() - start) * 1000)

            points = 0
            if task.award_points:
                try:
                    from services.competition import add_points
                    pts_result = add_points(task.agent_id, "task_completed", note=label[:80])
                    points = pts_result.get("points_added", 0)
                except Exception:
                    pass

            if progress is not None:
                progress[label] = {
                    "status": "done", "retries": retries,
                    "duration_ms": duration_ms,
                }

            return AgentResult(
                agent_id=task.agent_id, method=task.method,
                task_label=label, success=True, result=result,
                duration_ms=duration_ms, points_awarded=points, retries=retries,
            )

        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            retries += 1

            if retries > max_retries:
                break

            backoff = 2 ** retries
            if progress is not None:
                progress[label] = {
                    "status": f"retry_{retries}", "retries": retries,
                    "error": last_error, "backoff_s": backoff,
                }
            await asyncio.sleep(backoff)

    duration_ms = int((time.monotonic() - start) * 1000)
    if progress is not None:
        progress[label] = {
            "status": "failed", "retries": retries - 1,
            "error": last_error, "duration_ms": duration_ms,
        }
    return AgentResult(
        agent_id=task.agent_id, method=task.method,
        task_label=label, success=False, error=last_error,
        duration_ms=duration_ms, retries=retries - 1,
    )


async def run_agents_parallel(
    tasks: list[AgentTask],
    max_concurrent: int = 5,
    fail_fast: bool = False,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Exécute plusieurs tâches agents simultanément."""
    run_id = run_id or str(uuid.uuid4())[:8]
    semaphore = asyncio.Semaphore(max_concurrent)
    start_total = time.monotonic()

    progress: dict[str, Any] = {}
    _TASK_PROGRESS[run_id] = {
        "run_id": run_id, "total": len(tasks),
        "started_at": time.time(), "tasks": progress,
    }

    async def run_with_semaphore(task: AgentTask) -> AgentResult:
        async with semaphore:
            return await _run_single_task(task, run_id=run_id, progress=progress)

    if fail_fast:
        results = []
        for task in tasks:
            r = await run_with_semaphore(task)
            results.append(r)
            if not r.success:
                break
    else:
        results = await asyncio.gather(*[run_with_semaphore(t) for t in tasks])

    total_ms = int((time.monotonic() - start_total) * 1000)
    successes = [r for r in results if r.success]
    failures = [r for r in results if not r.success]
    durations = [r.duration_ms for r in results]

    _TASK_PROGRESS[run_id]["completed_at"] = time.time()
    _TASK_PROGRESS[run_id]["total_duration_ms"] = total_ms

    return {
        "run_id": run_id,
        "results": [
            {
                "agent_id": r.agent_id,
                "method": r.method,
                "label": r.task_label,
                "success": r.success,
                "result": r.result,
                "error": r.error,
                "duration_ms": r.duration_ms,
                "points_awarded": r.points_awarded,
                "retries": r.retries,
            }
            for r in results
        ],
        "success_count": len(successes),
        "failure_count": len(failures),
        "total_duration_ms": total_ms,
        "fastest_ms": min(durations) if durations else 0,
        "slowest_ms": max(durations) if durations else 0,
        "total_points_awarded": sum(r.points_awarded for r in results),
        "failed_tasks": [
            {"agent_id": r.agent_id, "method": r.method, "error": r.error}
            for r in failures
        ],
    }


def run_agents_parallel_sync(
    tasks: list[AgentTask],
    max_concurrent: int = 5,
    fail_fast: bool = False,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Version synchrone de run_agents_parallel."""
    coro = run_agents_parallel(tasks, max_concurrent, fail_fast, run_id)
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def run_with_dependencies(
    tasks: list[AgentTask],
    max_concurrent: int = 3,
) -> dict[str, Any]:
    """Exécute des tâches en respectant les dépendances (depends_on)."""
    completed: dict[str, AgentResult | dict] = {}
    pending = list(tasks)
    all_results: list[dict] = []
    start = time.monotonic()
    run_id = str(uuid.uuid4())[:8]

    _TASK_PROGRESS[run_id] = {
        "run_id": run_id, "total": len(tasks),
        "mode": "with_dependencies", "started_at": time.time(), "tasks": {},
    }

    while pending:
        ready = [t for t in pending if all(dep in completed for dep in t.depends_on)]
        if not ready:
            for t in pending:
                all_results.append({
                    "label": t.label, "success": False,
                    "error": "Blocked by dependency failure or cycle",
                    "agent_id": t.agent_id, "retries": 0,
                })
            break

        batch = ready[:max_concurrent]
        for t in batch:
            pending.remove(t)

        batch_result = run_agents_parallel_sync(batch, max_concurrent, run_id=run_id)
        for r in batch_result.get("results", []):
            completed[r["label"]] = r
            all_results.append(r)

    total_ms = int((time.monotonic() - start) * 1000)
    _TASK_PROGRESS[run_id]["completed_at"] = time.time()

    success_count = sum(1 for r in all_results if r.get("success"))
    return {
        "run_id": run_id,
        "results": all_results,
        "success_count": success_count,
        "failure_count": len(all_results) - success_count,
        "total_duration_ms": total_ms,
    }
