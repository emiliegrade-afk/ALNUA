"""Workflow engine — sequential recipe runner + RETRYABLE loop (DEC-024)."""

from __future__ import annotations

import inspect
import logging
import uuid
from typing import Any, Callable

from services.workflow_engine_catalog import get_recipe
from services.workflow_engine_handlers import _STEP_HANDLERS
from services.workflow_engine_models import StepRun, WorkflowRun, _now_iso
from services.workflow_engine_store import save_run

logger = logging.getLogger(__name__)


def _workflow_step_max_retries(recipe_id: str = "", step_id: str = "") -> int:
    try:
        from services.loop_engine import is_strict_loop, resolve_max_iterations

        strict = is_strict_loop(recipe_id=recipe_id, step_id=step_id)
        return resolve_max_iterations(strict=strict)
    except Exception:
        return 2 if (recipe_id or "").startswith("ship_") else 3


def _apply_handler(
    handler: Callable[..., dict[str, Any]],
    ctx: dict[str, Any],
    prior_steps: list[StepRun],
) -> dict[str, Any]:
    """Invoke handler with prior_steps when the signature accepts it."""
    sig = inspect.signature(handler)
    if len(sig.parameters) >= 2:
        return handler(ctx, prior_steps)
    return handler(ctx)


def run_workflow(recipe_id: str, context: dict[str, Any] | None = None) -> dict[str, Any]:
    """Execute a recipe sequentially; RETRYABLE re-runs step; ECART blocks human."""
    recipe = get_recipe(recipe_id)
    if not recipe:
        return {"success": False, "error": f"Recipe inconnue : {recipe_id}"}

    ctx = dict(context or {})
    ctx["_recipe_id"] = recipe_id
    if recipe_id == "ship_hub":
        ctx.setdefault("slug", "hub")
        ctx.setdefault("target_status", ctx.get("target_status", "prod"))
    if recipe_id == "ship_game":
        ctx.setdefault("target_status", ctx.get("target_status", "beta"))
        ctx.setdefault("max_open_errors", ctx.get("max_open_errors", 5))
    if recipe_id == "ship_robo":
        ctx.setdefault("target_status", ctx.get("target_status", "beta"))
        ctx.setdefault("max_open_errors", ctx.get("max_open_errors", 5))
    run = WorkflowRun(
        run_id=f"wf_{uuid.uuid4().hex[:12]}",
        recipe_id=recipe_id,
        context=ctx,
        steps=[StepRun(step_id=s.id, label=s.label) for s in recipe.steps],
    )
    ctx["_run_id"] = run.run_id
    save_run(run)

    prior: list[StepRun] = []
    blocked = False

    for i, step_def in enumerate(recipe.steps):
        step_run = run.steps[i]
        max_retries = _workflow_step_max_retries(recipe_id, step_def.id)
        handler = _STEP_HANDLERS.get(step_def.id)
        if not handler:
            step_run.status = "ECART"
            step_run.detail = f"Handler manquant : {step_def.id}"
            step_run.gaps = ["handler.missing"]
            step_run.finished_at = _now_iso()
            run.status = "blocked"
            run.blocked_at_step = step_def.id
            blocked = True
            break

        step_run.status = "IN_PROGRESS"
        step_run.started_at = _now_iso()
        save_run(run)

        attempt = 0
        feedback_log: list[str] = []
        outcome: dict[str, Any] = {"status": "ECART", "detail": "no outcome", "gaps": []}

        while attempt < max_retries:
            attempt += 1
            if feedback_log:
                ctx["_step_feedback"] = "\n\n".join(
                    f"[RETRY {idx + 1}] {fb}" for idx, fb in enumerate(feedback_log)
                )
                ctx["_step_iteration"] = attempt
            try:
                outcome = _apply_handler(handler, ctx, prior)
            except Exception as exc:
                logger.exception("workflow step %s failed", step_def.id)
                outcome = {
                    "status": "RETRYABLE",
                    "detail": str(exc),
                    "gaps": ["exception"],
                    "feedback": f"Exception: {type(exc).__name__}: {exc}",
                }

            status = outcome.get("status", "ECART")
            if status == "RETRYABLE":
                fb = str(
                    outcome.get("feedback")
                    or outcome.get("detail")
                    or "step retryable without detail"
                ).strip()
                feedback_log.append(fb[:2000])
                logger.warning(
                    "workflow %s step %s RETRYABLE iter %s/%s: %s",
                    run.run_id,
                    step_def.id,
                    attempt,
                    max_retries,
                    fb[:120],
                )
                if attempt >= max_retries:
                    outcome = {
                        "status": "ECART",
                        "detail": f"Escaladé après {max_retries} retries: {fb[:300]}",
                        "gaps": list(outcome.get("gaps") or []) + ["max_retries"],
                        "result": outcome.get("result"),
                    }
                    break
                continue
            break

        step_run.status = outcome.get("status", "ECART")
        step_run.detail = outcome.get("detail", "")
        step_run.gaps = outcome.get("gaps") or []
        step_run.result = outcome.get("result")
        if feedback_log:
            step_run.result = {
                **(step_run.result or {}),
                "_loop_feedback": feedback_log,
                "_loop_iterations": attempt,
            }
        step_run.finished_at = _now_iso()
        prior.append(step_run)

        try:
            from services.event_bus import emit

            emit(
                "workflow_step_completed",
                payload={
                    "run_id": run.run_id,
                    "recipe_id": recipe_id,
                    "step_id": step_def.id,
                    "status": step_run.status,
                    "detail": (step_run.detail or "")[:200],
                },
                source_agent=step_def.head_agent or recipe.head_agent,
            )
        except Exception:
            pass

        if step_run.status == "ECART":
            run.status = "blocked"
            run.blocked_at_step = step_def.id
            run.summary = f"Bloqué à {step_def.label} : {step_run.detail}"
            blocked = True
            break

        save_run(run)

    if not blocked:
        has_verify = any(s.status == "A_VERIFIER" for s in run.steps)
        run.status = "completed"
        run.summary = (
            "Terminé avec points à vérifier"
            if has_verify
            else f"Recette {recipe.name} terminée"
        )

    run.finished_at = _now_iso()
    save_run(run)

    return {
        "success": run.status == "completed",
        "blocked": run.status == "blocked",
        "run_id": run.run_id,
        "recipe_id": recipe_id,
        "status": run.status,
        "blocked_at_step": run.blocked_at_step,
        "summary": run.summary,
        "steps": [s.model_dump() for s in run.steps],
    }


def abort_workflow_run(
    run_id: str,
    *,
    agent_id: str,
    reason: str = "",
) -> dict[str, Any]:
    """Cancel a persisted workflow run — gated by workflow:abort."""
    from services.permission_guard import PermissionDeniedError, require_capability
    from services.workflow_engine_store import get_run

    try:
        require_capability(
            agent_id,
            "workflow:abort",
            resource=f"workflow:{run_id}",
            meta={"reason": (reason or "")[:120]},
        )
    except PermissionDeniedError as exc:
        return {"ok": False, "error": "capability_denied", "detail": str(exc)}

    run = get_run(run_id)
    if not run:
        return {"ok": False, "error": "not_found"}
    if run.status != "running":
        return {
            "ok": False,
            "error": "already_terminal",
            "status": run.status,
            "run_id": run_id,
        }

    note = (reason or "aborted").strip()[:200]
    run.status = "cancelled"
    run.summary = f"Aborted by {agent_id}: {note}"
    run.finished_at = _now_iso()
    for step in run.steps:
        if step.status in {"PENDING", "IN_PROGRESS", "RETRYABLE"}:
            step.status = "ECART"
            step.detail = f"aborted by {agent_id}"
            step.finished_at = run.finished_at
    save_run(run)
    return {
        "ok": True,
        "run_id": run_id,
        "status": "cancelled",
        "aborted_by": agent_id,
    }
