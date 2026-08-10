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
    """Run one step with linear backoff retries."""
    from services.parallel_runner import _get_agent_method

    start = time.time()
    retries = 0
    last_error = None

    while retries <= max_retries:
        try:
            method = _get_agent_method(step.agent_id, step.method)
            result = method(**step.kwargs)

            duration_ms = int((time.time() - start) * 1000)

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
                result=result,
                error=None,
                duration_ms=duration_ms,
                retries=retries,
            )

        except Exception as e:
            last_error = str(e)
            retries += 1
            if retries <= max_retries:
                time.sleep(retries * 2)
                logger.warning(f"Step {step.step_id} retry {retries}/{max_retries}: {e}")

    return StepResult(
        step_id=step.step_id,
        agent_id=step.agent_id,
        description=step.description,
        success=False,
        result=None,
        error=last_error,
        duration_ms=int((time.time() - start) * 1000),
        retries=retries - 1,
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
    """Full pipeline: objective → COO plan → execute."""
    logger.info(f"COO plan pipeline: {objective[:60]}")

    plan = parse_coo_plan(objective, context)

    if not plan.steps:
        return {
            "error": "COO n'a pas pu générer de plan",
            "objective": objective,
            "plan": plan.to_dict(),
            "results": [],
        }

    execution_result = execute_plan(
        plan,
        max_concurrent=max_concurrent,
        stop_on_failure=stop_on_failure,
    )

    return {
        "objective": objective,
        "plan": plan.to_dict(),
        **execution_result,
    }
