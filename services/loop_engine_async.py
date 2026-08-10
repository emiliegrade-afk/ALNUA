"""Async Loop Engine — execute → evaluate → feedback → retry."""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, TypeVar

from services.loop_engine_helpers import default_max_iterations, retry_sleep_s
from services.loop_engine_models import (
    EvalVerdict,
    IllegalTransitionError,
    LoopContext,
    LoopResult,
    LoopState,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")

ExecuteAsyncFn = Callable[[LoopContext], Awaitable[T]]
EvaluateAsyncFn = Callable[[T, LoopContext], Awaitable[EvalVerdict]]


async def run_loop_async(
    *,
    execute: ExecuteAsyncFn[T],
    evaluate: EvaluateAsyncFn[T],
    max_iterations: int | None = None,
    loop_id: str | None = None,
    meta: dict[str, Any] | None = None,
    sleep_s: float | None = None,
) -> LoopResult:
    """Async Loop Engine (fix_pipeline, etc.)."""
    from services.working_memory import end_loop_l4, sync_loop_l4

    cap = int(max_iterations if max_iterations is not None else default_max_iterations())
    state = LoopState.create(max_iterations=cap, loop_id=loop_id)
    pause = float(sleep_s if sleep_s is not None else retry_sleep_s())
    last_value: Any = None

    try:
        while True:
            try:
                state.advance_to_execution()
            except IllegalTransitionError:
                state.mark_escalated(
                    state.escalate_reason
                    or f"Max iterations exceeded ({state.max_iterations})"
                )
                break

            ctx = LoopContext(
                iteration=state.current_iteration,
                feedback_log=list(state.feedback_log),
                meta=dict(meta or {}),
            )
            try:
                last_value = await execute(ctx)
            except Exception as exc:
                state.submit_for_review()
                fb = f"Execute error: {type(exc).__name__}: {exc}"
                state.reject(fb)
                sync_loop_l4(state.loop_id, feedback=fb, attempt=state.current_iteration)
                logger.warning(
                    "loop_engine %s iter %s execute failed: %s",
                    state.loop_id,
                    state.current_iteration,
                    exc,
                )
                if state.current_iteration >= state.max_iterations:
                    state.mark_escalated(fb)
                    break
                if pause > 0:
                    await asyncio.sleep(pause)
                continue

            state.submit_for_review()
            try:
                verdict = await evaluate(last_value, ctx)
            except Exception as exc:
                state.fail_fatal(f"Evaluate error: {type(exc).__name__}: {exc}")
                break

            if verdict.approved:
                state.approve(detail=str(verdict.meta.get("detail") or "approved"))
                break

            if not verdict.retryable:
                state.fail_fatal(verdict.feedback)
                break

            state.reject(verdict.feedback)
            sync_loop_l4(
                state.loop_id,
                feedback=verdict.feedback,
                attempt=state.current_iteration,
            )
            if state.current_iteration >= state.max_iterations:
                state.mark_escalated(
                    f"Max iterations ({state.max_iterations}) with last feedback: "
                    f"{verdict.feedback[:200]}"
                )
                break
            if pause > 0:
                await asyncio.sleep(pause)
    finally:
        end_loop_l4(state.loop_id)

    return LoopResult(
        success=state.status == "COMPLETED",
        status=state.status,
        iterations=state.current_iteration,
        value=last_value if state.status == "COMPLETED" else None,
        feedback_log=list(state.feedback_log),
        escalate_reason=state.escalate_reason,
        loop_id=state.loop_id,
        attempts=[a.to_dict() for a in state.attempts],
    )
