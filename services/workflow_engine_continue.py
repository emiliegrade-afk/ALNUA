"""Workflow engine — resume runs after CEO approves A_VERIFIER steps."""

from __future__ import annotations

import logging
from typing import Any

from services.workflow_engine_catalog import get_recipe
from services.workflow_engine_handlers import _STEP_HANDLERS
from services.workflow_engine_models import StepRun, WorkflowRun, _now_iso
from services.workflow_engine_run import _apply_handler
from services.workflow_engine_store import get_run, save_run

logger = logging.getLogger(__name__)


def _rebuild_ctx(run: WorkflowRun) -> dict[str, Any]:
    ctx = dict(run.context)
    ctx["_run_id"] = run.run_id
    ctx["_recipe_id"] = run.recipe_id
    artifact = ctx.get("artifact")
    if isinstance(artifact, dict):
        ctx["_loaded_artifact"] = artifact
    for step in run.steps:
        if step.step_id == "quality_gate" and step.result:
            ctx["_gate_decision"] = step.result
    return ctx


def continue_workflow_run(
    run_id: str,
    *,
    from_step_index: int = 0,
    ceo_approved: bool = False,
) -> dict[str, Any]:
    """Re-invoke handlers for remaining A_VERIFIER steps (after CEO approval)."""
    run = get_run(run_id)
    if not run:
        return {"ok": False, "error": "not_found", "run_id": run_id}

    recipe = get_recipe(run.recipe_id)
    if not recipe:
        return {"ok": False, "error": "recipe_not_found", "recipe_id": run.recipe_id}

    ctx = _rebuild_ctx(run)
    if ceo_approved:
        ctx["_ceo_approved"] = True

    prior: list[StepRun] = [s for s in run.steps[:from_step_index] if s.status == "OK"]
    blocked = False
    run.status = "running"
    run.blocked_at_step = None

    for i in range(from_step_index, len(recipe.steps)):
        step_run = run.steps[i]
        if step_run.status == "OK":
            if step_run not in prior:
                prior.append(step_run)
            continue
        if step_run.status != "A_VERIFIER":
            if step_run.status == "ECART":
                blocked = True
            continue

        handler = _STEP_HANDLERS.get(step_run.step_id)
        if not handler:
            step_run.status = "ECART"
            step_run.detail = f"Handler manquant : {step_run.step_id}"
            blocked = True
            break

        step_run.status = "IN_PROGRESS"
        step_run.started_at = step_run.started_at or _now_iso()
        save_run(run)

        try:
            outcome = _apply_handler(handler, ctx, prior)
        except Exception as exc:
            logger.exception("workflow continue step %s failed", step_run.step_id)
            outcome = {"status": "ECART", "detail": str(exc), "gaps": ["exception"]}

        step_run.status = outcome.get("status", "ECART")
        step_run.detail = outcome.get("detail", step_run.detail)
        step_run.gaps = outcome.get("gaps") or []
        if outcome.get("result") is not None:
            step_run.result = outcome.get("result")
        step_run.finished_at = _now_iso()
        prior.append(step_run)

        if step_run.status == "ECART":
            run.status = "blocked"
            run.blocked_at_step = step_run.step_id
            run.summary = f"Bloqué à {step_run.label} : {step_run.detail}"
            blocked = True
            break
        save_run(run)

    if not blocked:
        has_verify = any(s.status == "A_VERIFIER" for s in run.steps)
        run.status = "completed"
        run.summary = (
            "Terminé avec points à vérifier"
            if has_verify
            else f"Recette {recipe.name} terminée (reprise CEO)"
        )

    run.finished_at = _now_iso()
    save_run(run)

    return {
        "ok": True,
        "success": run.status == "completed",
        "blocked": run.status == "blocked",
        "run_id": run.run_id,
        "recipe_id": run.recipe_id,
        "status": run.status,
        "blocked_at_step": run.blocked_at_step,
        "summary": run.summary,
        "steps": [s.model_dump() for s in run.steps],
    }


def approve_workflow_step(
    run_id: str,
    step_id: str,
    *,
    approver_agent_id: str = "ceo",
) -> dict[str, Any]:
    """CEO approves one A_VERIFIER step and continues the run."""
    run = get_run(run_id)
    if not run:
        return {"ok": False, "error": "not_found", "run_id": run_id}

    step_idx = next((i for i, s in enumerate(run.steps) if s.step_id == step_id), None)
    if step_idx is None:
        return {"ok": False, "error": "step_not_found", "step_id": step_id}

    step = run.steps[step_idx]
    if step.status != "A_VERIFIER":
        return {
            "ok": False,
            "error": "not_a_verifier",
            "step_id": step_id,
            "status": step.status,
        }

    ctx = _rebuild_ctx(run)
    ctx["_ceo_approved"] = True
    handler = _STEP_HANDLERS.get(step_id)
    if not handler:
        return {"ok": False, "error": "handler_missing", "step_id": step_id}

    prior = [s for s in run.steps[:step_idx] if s.status == "OK"]
    step.status = "IN_PROGRESS"
    save_run(run)

    try:
        outcome = _apply_handler(handler, ctx, prior)
    except Exception as exc:
        logger.exception("workflow approve step %s failed", step_id)
        return {"ok": False, "error": "handler_failed", "detail": str(exc)}

    approved_status = outcome.get("status", "ECART")
    if approved_status == "A_VERIFIER":
        return {
            "ok": False,
            "error": "still_a_verifier",
            "detail": outcome.get("detail", "Step still requires verification"),
        }

    step.status = approved_status
    step.detail = outcome.get("detail") or f"Approuvé par {approver_agent_id}"
    step.gaps = outcome.get("gaps") or []
    if outcome.get("result") is not None:
        step.result = outcome.get("result")
    step.finished_at = _now_iso()
    save_run(run)

    if approved_status == "ECART":
        run.status = "blocked"
        run.blocked_at_step = step_id
        run.summary = f"Bloqué à {step.label} : {step.detail}"
        run.finished_at = _now_iso()
        save_run(run)
        return {
            "ok": False,
            "error": "step_ecart",
            "run_id": run_id,
            "step_id": step_id,
            "detail": step.detail,
        }

    continued = continue_workflow_run(run_id, from_step_index=step_idx + 1, ceo_approved=True)
    continued["approved_step_id"] = step_id
    continued["approved_by"] = approver_agent_id
    return continued


def reject_workflow_step(
    run_id: str,
    step_id: str,
    *,
    rejector_agent_id: str = "ceo",
    reason: str = "",
) -> dict[str, Any]:
    """CEO rejects an A_VERIFIER step — stop the run, do not continue."""
    run = get_run(run_id)
    if not run:
        return {"ok": False, "error": "not_found", "run_id": run_id}

    step_idx = next((i for i, s in enumerate(run.steps) if s.step_id == step_id), None)
    if step_idx is None:
        return {"ok": False, "error": "step_not_found", "step_id": step_id}

    step = run.steps[step_idx]
    if step.status != "A_VERIFIER":
        return {
            "ok": False,
            "error": "not_a_verifier",
            "step_id": step_id,
            "status": step.status,
        }

    note = (reason or "Refusé par le CEO").strip()[:400]
    step.status = "ECART"
    step.detail = f"Rejeté par {rejector_agent_id}: {note}"
    step.gaps = list(step.gaps or []) + ["ceo_rejected"]
    step.finished_at = _now_iso()

    for later in run.steps[step_idx + 1 :]:
        if later.status in {"PENDING", "IN_PROGRESS", "RETRYABLE", "A_VERIFIER"}:
            later.status = "ECART"
            later.detail = f"Annulé — étape {step_id} rejetée par {rejector_agent_id}"
            later.finished_at = step.finished_at

    run.status = "cancelled"
    run.blocked_at_step = step_id
    run.summary = f"Rejeté par {rejector_agent_id} à « {step.label} » : {note}"
    run.finished_at = step.finished_at
    save_run(run)

    return {
        "ok": True,
        "success": False,
        "blocked": True,
        "rejected": True,
        "run_id": run.run_id,
        "recipe_id": run.recipe_id,
        "status": run.status,
        "blocked_at_step": run.blocked_at_step,
        "summary": run.summary,
        "rejected_step_id": step_id,
        "rejected_by": rejector_agent_id,
        "steps": [s.model_dump() for s in run.steps],
    }