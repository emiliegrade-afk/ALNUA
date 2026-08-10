"""Workflow engine — sequential recipe runner."""

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
    """Execute a recipe sequentially; stop on ECART."""
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
        steps=[
            StepRun(step_id=s.id, label=s.label) for s in recipe.steps
        ],
    )
    save_run(run)

    prior: list[StepRun] = []
    blocked = False

    for i, step_def in enumerate(recipe.steps):
        step_run = run.steps[i]
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

        try:
            outcome = _apply_handler(handler, ctx, prior)
        except Exception as exc:
            logger.exception("workflow step %s failed", step_def.id)
            outcome = {"status": "ECART", "detail": str(exc), "gaps": ["exception"]}

        step_run.status = outcome.get("status", "ECART")
        step_run.detail = outcome.get("detail", "")
        step_run.gaps = outcome.get("gaps") or []
        step_run.result = outcome.get("result")
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
