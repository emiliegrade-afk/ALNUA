"""Plan executor — step execution with dependency-aware batching."""

from __future__ import annotations

import concurrent.futures
import logging
import time
from datetime import datetime, timezone
from typing import Any

from services.plan_executor_models import ExecutionPlan, ExecutionStep, StepResult
from services.plan_executor_parser import parse_coo_plan

logger = logging.getLogger(__name__)


def _execute_step(step: ExecutionStep, max_retries: int = 2) -> StepResult:
    """Run one step via Loop Engine (feedback retry) + Phase A isolation."""
    from services.agent_isolation import task_isolation
    from services.loop_engine import (
        EvalVerdict,
        LoopContext,
        is_strict_loop,
        resolve_max_iterations,
        run_loop,
    )
    from services.parallel_runner import _get_agent_method

    start = time.time()
    # max_retries=2 → up to 3 attempts (legacy); merge/destructive → strict ceiling
    legacy_cap = max(1, int(max_retries) + 1)
    strict = is_strict_loop(
        agent_id=step.agent_id,
        method=step.method,
        step_id=step.step_id,
        kwargs=step.kwargs,
    )
    cap = resolve_max_iterations(strict=strict, override=legacy_cap)
    holder = f"plan:{step.step_id}"

    def execute(ctx: LoopContext) -> Any:
        from services.working_memory import set_working_memory

        kwargs = dict(step.kwargs or {})
        if ctx.feedback_log:
            fb = ctx.feedback_block(max_chars=2000)
            kwargs["_loop_feedback"] = fb
            kwargs["_loop_iteration"] = ctx.iteration
            set_working_memory(
                holder,
                agent_id=step.agent_id,
                feedback=fb,
                attempt=ctx.iteration,
            )
        kwargs["_context_task_id"] = holder
        with task_isolation(
            agent_id=step.agent_id,
            holder_id=f"{holder}:i{ctx.iteration}",
            lock_keys=list(step.lock_keys or []),
            kwargs=kwargs,
            repo_path=step.repo_path or None,
            repo_slug=step.repo_slug or None,
            meta={"step_id": step.step_id, "method": step.method, "iter": ctx.iteration},
        ):
            method = _get_agent_method(step.agent_id, step.method)
            return method(**kwargs)

    def evaluate(value: Any, ctx: LoopContext) -> EvalVerdict:
        # Structured failure dict from agents
        if isinstance(value, dict) and value.get("success") is False:
            fb = str(value.get("error") or value.get("summary") or "step returned success=false")
            return EvalVerdict(approved=False, feedback=fb[:2000])
        return EvalVerdict(approved=True, meta={"detail": "ok"})

    try:
        loop_result = run_loop(
            execute=execute,
            evaluate=evaluate,
            max_iterations=cap,
            loop_id=holder,
            sleep_s=0.0,
        )
    finally:
        try:
            from services.working_memory import wipe_working_memory

            wipe_working_memory(holder)
        except Exception:
            pass
    duration_ms = int((time.time() - start) * 1000)
    retries_used = max(0, loop_result.iterations - 1)

    if loop_result.success:
        if step.award_points:
            try:
                from services.competition import add_points

                add_points(
                    step.agent_id,
                    "task_completed",
                    note=f"Plan step: {step.description[:50]}",
                )
            except Exception:
                pass
        return StepResult(
            step_id=step.step_id,
            agent_id=step.agent_id,
            description=step.description,
            success=True,
            result=loop_result.value,
            error=None,
            duration_ms=duration_ms,
            retries=retries_used,
        )

    err = loop_result.escalate_reason or (
        loop_result.feedback_log[-1] if loop_result.feedback_log else "loop failed"
    )
    return StepResult(
        step_id=step.step_id,
        agent_id=step.agent_id,
        description=step.description,
        success=False,
        result=None,
        error=err,
        duration_ms=duration_ms,
        retries=retries_used,
    )


def execute_plan(
    plan: ExecutionPlan,
    max_concurrent: int = 4,
    stop_on_failure: bool = False,
    max_retries: int = 2,
) -> dict[str, Any]:
    """Execute a plan respecting depends_on; independent steps run in parallel."""
    if not plan.steps:
        return {
            "plan_id": plan.plan_id,
            "title": plan.title,
            "error": "Plan vide — aucune étape à exécuter",
            "results": [],
        }

    completed: dict[str, StepResult] = {}
    all_results: list[StepResult] = []
    pending = list(plan.steps)
    start_total = time.time()

    logger.info(f"Executing plan '{plan.title}' — {len(plan.steps)} steps")

    while pending:
        ready = [
            s
            for s in pending
            if all(dep in completed for dep in s.depends_on)
            and (
                not stop_on_failure
                or all(completed[dep].success for dep in s.depends_on)
            )
        ]

        if not ready:
            remaining_ids = [s.step_id for s in pending]
            logger.warning(f"Plan stalled — remaining: {remaining_ids}")
            for s in pending:
                all_results.append(
                    StepResult(
                        step_id=s.step_id,
                        agent_id=s.agent_id,
                        description=s.description,
                        success=False,
                        result=None,
                        error="Blocked by dependency failure or cycle",
                        duration_ms=0,
                    )
                )
            break

        batch = ready[:max_concurrent]
        for s in batch:
            pending.remove(s)

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(batch)) as executor:
            futures = {
                executor.submit(_execute_step, s, max_retries): s for s in batch
            }
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                completed[result.step_id] = result
                all_results.append(result)
                logger.info(
                    f"Step {result.step_id} {'✅' if result.success else '❌'} "
                    f"({result.duration_ms}ms, {result.retries} retries)"
                )

    total_ms = int((time.time() - start_total) * 1000)
    success_count = sum(1 for r in all_results if r.success)

    if success_count == len(plan.steps):
        try:
            from services.competition import add_points

            add_points("coo", "task_validated", note=f"Plan completed: {plan.title[:50]}")
        except Exception:
            pass

    return {
        "plan_id": plan.plan_id,
        "title": plan.title,
        "objective": plan.objective,
        "total_steps": len(plan.steps),
        "success_count": success_count,
        "failure_count": len(all_results) - success_count,
        "total_duration_ms": total_ms,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "results": [r.to_dict() for r in all_results],
        "plan_summary": {s.step_id: s.to_dict() for s in plan.steps},
    }


def run_coo_plan(
    objective: str,
    context: str = "",
    max_concurrent: int = 4,
    stop_on_failure: bool = False,
) -> dict[str, Any]:
    """Full pipeline: objective → COO plan → Mission Graph execute (DEC-023)."""
    logger.info(f"COO plan pipeline: {objective[:60]}")

    plan = parse_coo_plan(objective, context)

    if not plan.steps:
        return {
            "error": "COO n'a pas pu générer de plan",
            "objective": objective,
            "plan": plan.to_dict(),
            "results": [],
        }

    from services.mission_graph_build import mission_from_plan
    from services.mission_graph_run import run_mission
    from services.mission_graph_store import get_mission

    mission = mission_from_plan(plan, source="coo_plan", persist=True)
    run_result = run_mission(
        mission.mission_id,
        max_concurrent=max_concurrent,
        stop_on_failure=stop_on_failure,
    )
    fresh = get_mission(mission.mission_id)
    tasks = (fresh.tasks if fresh else mission.tasks)
    success_count = sum(1 for t in tasks if t.status == "COMPLETED")
    results = [
        {
            "step_id": t.task_id,
            "agent_id": t.agent_id,
            "description": t.description,
            "success": t.status == "COMPLETED",
            "result": t.result,
            "error": t.error,
            "duration_ms": t.duration_ms,
            "retries": t.retries,
        }
        for t in tasks
    ]

    return {
        "objective": objective,
        "plan": plan.to_dict(),
        "plan_id": plan.plan_id,
        "mission_id": mission.mission_id,
        "title": plan.title,
        "total_steps": len(plan.steps),
        "success_count": success_count,
        "failure_count": len(tasks) - success_count,
        "total_duration_ms": sum(t.duration_ms for t in tasks),
        "completed_at": (fresh.finished_at if fresh else None),
        "results": results,
        "plan_summary": {s.step_id: s.to_dict() for s in plan.steps},
        "mission_status": run_result.get("status"),
        "graph": run_result.get("graph"),
    }
