"""Validation recipes for Phase 30 — extend workflow_engine without growing it.

Recipes: content_validation, campaign_validation.
Autonomy 0–3 controls how many post-load steps may auto-OK (vs A_VERIFIER).
"""

from __future__ import annotations

import logging
from typing import Any

from services.workflow_engine import WorkflowRecipe, WorkflowStepDef

logger = logging.getLogger(__name__)

# How many of [quality_gate, apply_trust, emit_validated] may auto-OK.
_AUTONOMY_AUTO_COUNT = {0: 0, 1: 1, 2: 2, 3: 3}

VALIDATION_RECIPES: list[WorkflowRecipe] = [
    WorkflowRecipe(
        id="content_validation",
        name="Validation contenu",
        description="Gate qualité contenu → trust producteur → event content_validated.",
        head_agent="content",
        priority="P1",
        steps=[
            WorkflowStepDef(id="load_artifact", label="Charger artefact", head_agent="content"),
            WorkflowStepDef(id="quality_gate", label="Quality gate département", head_agent="qa"),
            WorkflowStepDef(id="apply_trust", label="Mettre à jour trust", head_agent="qa"),
            WorkflowStepDef(id="emit_validated", label="Émettre content_validated", head_agent="content"),
        ],
    ),
    WorkflowRecipe(
        id="campaign_validation",
        name="Validation campagne",
        description="Gate qualité marketing → trust → event campaign_validated.",
        head_agent="ads",
        priority="P1",
        steps=[
            WorkflowStepDef(id="load_artifact", label="Charger artefact", head_agent="ads"),
            WorkflowStepDef(id="quality_gate", label="Quality gate département", head_agent="marketing"),
            WorkflowStepDef(id="apply_trust", label="Mettre à jour trust", head_agent="qa"),
            WorkflowStepDef(id="emit_validated", label="Émettre campaign_validated", head_agent="ads"),
        ],
    ),
]


def _clamp_autonomy(raw: Any) -> int:
    try:
        level = int(raw)
    except (TypeError, ValueError):
        level = 1
    return max(0, min(3, level))


def _auto_ok_allowed(ctx: dict[str, Any], step_index_after_load: int) -> bool:
    """step_index_after_load: 0=quality_gate, 1=apply_trust, 2=emit_validated."""
    level = _clamp_autonomy(ctx.get("autonomy_level", 1))
    return step_index_after_load < _AUTONOMY_AUTO_COUNT[level]


def _default_department(ctx: dict[str, Any], recipe_hint: str) -> str:
    dept = str(ctx.get("department") or "").strip().lower()
    if dept:
        return dept
    return recipe_hint


def _step_load_artifact(ctx: dict[str, Any]) -> dict[str, Any]:
    artifact = ctx.get("artifact")
    if not isinstance(artifact, dict):
        return {
            "status": "ECART",
            "detail": "context.artifact (dict) requis",
            "gaps": ["artifact.missing"],
        }
    title = str(artifact.get("title") or artifact.get("name") or "").strip()
    if len(title) < 1:
        return {
            "status": "ECART",
            "detail": "artifact.title (ou name) requis",
            "gaps": ["artifact.title"],
        }
    ctx["_loaded_artifact"] = artifact
    return {
        "status": "OK",
        "detail": f"Artefact chargé : {title[:80]}",
        "result": {"title": title[:120]},
    }


def _step_quality_gate(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.review_board import evaluate_submission

    artifact = ctx.get("_loaded_artifact") or ctx.get("artifact") or {}
    recipe_id = str(ctx.get("_recipe_id") or "")
    hint = "content" if recipe_id == "content_validation" else "marketing"
    department = _default_department(ctx, hint)
    producer = str(ctx.get("producer_agent_id") or artifact.get("producer_agent_id") or "").strip()

    # Gate only — trust recorded in apply_trust step
    decision = evaluate_submission(
        department=department,
        artifact=dict(artifact),
        producer_agent_id=producer or None,
        record_trust=False,
    )
    ctx["_gate_decision"] = decision

    if not decision["gate_open"]:
        return {
            "status": "ECART",
            "detail": (
                f"Gate fermée score={decision['score']} "
                f"< seuil={decision['threshold']} ({department})"
            ),
            "gaps": ["quality_gate.closed"],
            "result": decision,
        }

    if not _auto_ok_allowed(ctx, 0):
        return {
            "status": "A_VERIFIER",
            "detail": "Gate ouverte — autonomie 0, validation humaine requise",
            "result": decision,
        }
    return {
        "status": "OK",
        "detail": f"Gate ouverte score={decision['score']}/{decision['threshold']}",
        "result": decision,
    }


def _step_apply_trust(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.agent_trust import record_validation

    decision = ctx.get("_gate_decision") or {}
    artifact = ctx.get("_loaded_artifact") or {}
    producer = str(
        ctx.get("producer_agent_id") or artifact.get("producer_agent_id") or ""
    ).strip()
    gate_open = bool(decision.get("gate_open"))

    if not producer:
        return {
            "status": "A_VERIFIER",
            "detail": "Pas de producer_agent_id — trust non mis à jour",
            "gaps": ["producer.missing"],
            "result": {"skipped": True},
        }

    if not _auto_ok_allowed(ctx, 1):
        return {
            "status": "A_VERIFIER",
            "detail": "Trust en attente (autonomie insuffisante)",
            "result": {"producer_agent_id": producer, "pending": True},
        }

    row = record_validation(
        producer,
        success=gate_open,
        weight=1.0,
        note=f"workflow:{ctx.get('_recipe_id', 'validation')}",
        source="workflow_validation",
    )
    return {
        "status": "OK",
        "detail": f"Trust {producer} → {row.get('score')}",
        "result": row,
    }


def _step_emit_validated(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.event_bus import emit

    recipe_id = str(ctx.get("_recipe_id") or "")
    event_type = (
        "campaign_validated" if recipe_id == "campaign_validation" else "content_validated"
    )
    decision = ctx.get("_gate_decision") or {}
    if not decision.get("gate_open"):
        return {
            "status": "ECART",
            "detail": "Pas d'émission — gate non ouverte",
            "gaps": ["emit.gate_closed"],
        }

    if not _auto_ok_allowed(ctx, 2):
        return {
            "status": "A_VERIFIER",
            "detail": f"Émission {event_type} différée (autonomie)",
            "result": {"event_type": event_type, "pending": True},
        }

    artifact = ctx.get("_loaded_artifact") or {}
    payload = {
        "recipe_id": recipe_id,
        "department": decision.get("department"),
        "score": decision.get("score"),
        "title": artifact.get("title") or artifact.get("name"),
        "producer_agent_id": ctx.get("producer_agent_id"),
        "project_id": ctx.get("project_id") or artifact.get("project_id"),
        "campaign_id": ctx.get("campaign_id") or artifact.get("campaign_id"),
    }
    emit(event_type, payload=payload, source_agent=str(ctx.get("producer_agent_id") or "workflow"))
    # Also fan-out project_validated when a project_id is present
    if payload.get("project_id"):
        emit(
            "project_validated",
            payload=payload,
            source_agent=str(ctx.get("producer_agent_id") or "workflow"),
        )
    return {
        "status": "OK",
        "detail": f"Émis {event_type}",
        "result": {"event_type": event_type, "payload": payload},
    }


VALIDATION_HANDLERS: dict[str, Any] = {
    "load_artifact": _step_load_artifact,
    "quality_gate": _step_quality_gate,
    "apply_trust": _step_apply_trust,
    "emit_validated": _step_emit_validated,
}


def register_validation_recipes() -> None:
    """Idempotent registration into workflow_engine catalogues."""
    from services import workflow_engine as we

    existing = {r.id for r in we.RECIPE_CATALOG}
    for recipe in VALIDATION_RECIPES:
        if recipe.id not in existing:
            we.RECIPE_CATALOG.append(recipe)
            existing.add(recipe.id)
    # Shared step ids — safe to overwrite with same handlers
    we._STEP_HANDLERS.update(VALIDATION_HANDLERS)
    logger.info(
        "workflow_validation_recipes registered: %s",
        [r.id for r in VALIDATION_RECIPES],
    )
