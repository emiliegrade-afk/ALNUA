"""ALNUA Workflow Engine — Hermes-lite recipe runner with ECART blocking."""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Literal

from pydantic import BaseModel, Field

from config.paths import get_hub_repo_path
from services.workflow_step_handlers_dossier import (
    _step_control_gaps,
    _step_generate_package,
    _step_mark_ready,
    _step_validate_committee,
    _step_validate_sections,
)
from services.workflow_step_handlers_ops import (
    _step_ceo_queue_reminder,
    _step_cost_snapshot,
    _step_ingest_beta_feedback,
    _step_ops_snapshot,
    _step_remediate_errors,
    _step_sav_ceo_pending,
    _step_scan_errors,
    _step_scan_registry,
    _step_start_investigation,
    _step_sync_product_kb,
    _step_watchdog_status,
    _step_weekly_briefing,
)
from services.workflow_step_handlers_ship import (
    _step_notify_shipped,
    _step_qa_readiness,
    _step_update_lifecycle,
    _step_validate_gaming_readiness,
    _step_validate_registry,
    _step_validate_registry_gaming,
    _step_validate_registry_robotics,
    _step_validate_robotics_readiness,
)

logger = logging.getLogger(__name__)

StepStatus = Literal["PENDING", "IN_PROGRESS", "OK", "A_VERIFIER", "ECART"]
RunStatus = Literal["running", "completed", "blocked", "failed"]

_RUNS_DIR = get_hub_repo_path() / "data" / "workflow_runs"


class WorkflowStepDef(BaseModel):
    id: str
    label: str
    head_agent: str = "coo"


class WorkflowRecipe(BaseModel):
    id: str
    name: str
    description: str
    head_agent: str
    steps: list[WorkflowStepDef]
    priority: str = "P0"


class StepRun(BaseModel):
    step_id: str
    label: str
    status: StepStatus = "PENDING"
    detail: str = ""
    gaps: list[str] = Field(default_factory=list)
    started_at: str | None = None
    finished_at: str | None = None
    result: dict[str, Any] | None = None


class WorkflowRun(BaseModel):
    run_id: str
    recipe_id: str
    context: dict[str, Any] = Field(default_factory=dict)
    status: RunStatus = "running"
    steps: list[StepRun] = Field(default_factory=list)
    blocked_at_step: str | None = None
    created_at: str = Field(default_factory=lambda: _now_iso())
    finished_at: str | None = None
    summary: str = ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Recipe catalogue
# ---------------------------------------------------------------------------

RECIPE_CATALOG: list[WorkflowRecipe] = [
    WorkflowRecipe(
        id="dossier_ceo",
        name="Dossier R&D → Package CEO",
        description="Valide le dossier, génère le package CEO, contrôle les écarts, marque ready_for_ceo.",
        head_agent="rnd_ceo_agent",
        steps=[
            WorkflowStepDef(id="validate_sections", label="Sections obligatoires validées", head_agent="rnd_ceo_agent"),
            WorkflowStepDef(id="validate_committee", label="Compte-rendu comité", head_agent="rnd_ceo_agent"),
            WorkflowStepDef(id="generate_package", label="Génération package CEO", head_agent="rnd_ceo_agent"),
            WorkflowStepDef(id="control_gaps", label="Contrôle indépendant (écarts)", head_agent="rnd_ceo_agent"),
            WorkflowStepDef(id="mark_ready", label="Marquer ready_for_ceo", head_agent="rnd_ceo_agent"),
        ],
    ),
    WorkflowRecipe(
        id="ship_app",
        name="Release application",
        description="Valide le registry, contrôle QA, met à jour lifecycle_status, notifie feature_shipped.",
        head_agent="qa",
        steps=[
            WorkflowStepDef(id="validate_registry", label="App dans le registry", head_agent="qa"),
            WorkflowStepDef(id="qa_readiness", label="Erreurs coding ouvertes", head_agent="qa"),
            WorkflowStepDef(id="update_lifecycle", label="Mise à jour lifecycle", head_agent="coo"),
            WorkflowStepDef(id="notify_shipped", label="Événement feature_shipped", head_agent="coo"),
        ],
    ),
    WorkflowRecipe(
        id="ship_hub",
        name="Release amélioration Hub (infra interne)",
        description="Valide le registry hub, QA, lifecycle build→prod sur ALNUA_HUB.",
        head_agent="qa",
        steps=[
            WorkflowStepDef(id="validate_registry", label="Hub dans le registry", head_agent="qa"),
            WorkflowStepDef(id="qa_readiness", label="Erreurs coding ouvertes", head_agent="qa"),
            WorkflowStepDef(id="update_lifecycle", label="Mise à jour lifecycle", head_agent="coo"),
            WorkflowStepDef(id="notify_shipped", label="Événement feature_shipped", head_agent="coo"),
        ],
    ),
    WorkflowRecipe(
        id="run_ops",
        name="RUN — surveillance multi-repo",
        description="Scan registry, erreurs unifiées, watchdog, auto-issues si activé.",
        head_agent="coo",
        steps=[
            WorkflowStepDef(id="scan_registry", label="Apps actives du registry", head_agent="coo"),
            WorkflowStepDef(id="scan_errors", label="Erreurs ouvertes (unifiées)", head_agent="coo"),
            WorkflowStepDef(id="watchdog_status", label="Couverture watchdog", head_agent="coo"),
            WorkflowStepDef(id="remediate_errors", label="Auto-issues GitHub (ops)", head_agent="coo"),
        ],
    ),
    WorkflowRecipe(
        id="semaine",
        name="Brief hebdo ops (CEO garde les décisions produit)",
        description="Briefing COO + ops + rappel queue CEO — sans décider à ta place.",
        head_agent="coo",
        steps=[
            WorkflowStepDef(id="weekly_briefing", label="Briefing COO", head_agent="coo"),
            WorkflowStepDef(id="ops_snapshot", label="Snapshot ops multi-repo", head_agent="coo"),
            WorkflowStepDef(id="ceo_queue_reminder", label="Dossiers en attente validation CEO", head_agent="coo"),
            WorkflowStepDef(id="cost_snapshot", label="Coûts LLM 7 jours", head_agent="accounting"),
        ],
    ),
    WorkflowRecipe(
        id="explore",
        name="EXPLORE — Arbres R&D",
        description="Délègue à rnd_hypothesis_tree.start_investigation (arbor-lite).",
        head_agent="rnd_agent",
        steps=[
            WorkflowStepDef(id="start_investigation", label="Lancer arbre d'hypothèses", head_agent="rnd_agent"),
        ],
        priority="done",
    ),
    WorkflowRecipe(
        id="sav_lite",
        name="SAV lite — tri Nadia + validation CEO",
        description="Sync KB produits, ingest feedback beta, brouillons réponses, alerte CEO si sensible.",
        head_agent="secretary",
        priority="P1",
        steps=[
            WorkflowStepDef(id="sync_product_kb", label="Sync KB depuis registry", head_agent="secretary"),
            WorkflowStepDef(id="ingest_beta_feedback", label="Ingest feedback beta récent", head_agent="secretary"),
            WorkflowStepDef(id="sav_ceo_pending", label="Cas en attente validation CEO", head_agent="secretary"),
        ],
    ),
    WorkflowRecipe(
        id="ship_game",
        name="Release jeu (Godot / GDD)",
        description="Registry gaming, readiness GDD+Godot, QA, lifecycle, feature_shipped.",
        head_agent="game_director",
        priority="P2",
        steps=[
            WorkflowStepDef(id="validate_registry_gaming", label="Projet gaming dans registry", head_agent="game_director"),
            WorkflowStepDef(id="validate_gaming_readiness", label="GDD + projet Godot", head_agent="game_director"),
            WorkflowStepDef(id="qa_readiness", label="Erreurs coding ouvertes", head_agent="qa"),
            WorkflowStepDef(id="update_lifecycle", label="Mise à jour lifecycle", head_agent="coo"),
            WorkflowStepDef(id="notify_shipped", label="Événement feature_shipped", head_agent="coo"),
        ],
    ),
    WorkflowRecipe(
        id="ship_robo",
        name="Release robotique (hardware)",
        description="Registry robotics, brief hardware/BOM, QA, lifecycle, feature_shipped.",
        head_agent="hardware",
        priority="P2",
        steps=[
            WorkflowStepDef(id="validate_registry_robotics", label="Projet robotics dans registry", head_agent="hardware"),
            WorkflowStepDef(id="validate_robotics_readiness", label="Brief hardware / BOM", head_agent="hardware"),
            WorkflowStepDef(id="qa_readiness", label="Erreurs coding ouvertes", head_agent="qa"),
            WorkflowStepDef(id="update_lifecycle", label="Mise à jour lifecycle", head_agent="coo"),
            WorkflowStepDef(id="notify_shipped", label="Événement feature_shipped", head_agent="coo"),
        ],
    ),
]


def list_recipes() -> list[dict[str, Any]]:
    return [r.model_dump() for r in RECIPE_CATALOG]


def get_recipe(recipe_id: str) -> WorkflowRecipe | None:
    return next((r for r in RECIPE_CATALOG if r.id == recipe_id), None)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def _runs_dir() -> Path:
    _RUNS_DIR.mkdir(parents=True, exist_ok=True)
    return _RUNS_DIR


def save_run(run: WorkflowRun) -> Path:
    path = _runs_dir() / f"{run.run_id}.json"
    path.write_text(json.dumps(run.model_dump(), indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def get_run(run_id: str) -> WorkflowRun | None:
    path = _runs_dir() / f"{run_id}.json"
    if not path.exists():
        return None
    try:
        return WorkflowRun.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except Exception as exc:
        logger.warning("workflow get_run failed: %s", exc)
        return None


def list_runs(*, limit: int = 30, recipe_id: str | None = None) -> list[dict[str, Any]]:
    items: list[tuple[str, WorkflowRun]] = []
    for path in sorted(_runs_dir().glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            run = WorkflowRun.model_validate(json.loads(path.read_text(encoding="utf-8")))
            if recipe_id and run.recipe_id != recipe_id:
                continue
            items.append((path.name, run))
        except Exception:
            continue
        if len(items) >= limit:
            break
    return [
        {
            "run_id": run.run_id,
            "recipe_id": run.recipe_id,
            "status": run.status,
            "blocked_at_step": run.blocked_at_step,
            "created_at": run.created_at,
            "finished_at": run.finished_at,
            "summary": run.summary[:200],
        }
        for _, run in items
    ]


# ---------------------------------------------------------------------------
# Step handler registry (handlers in workflow_step_handlers_* — BUG-004)
# ---------------------------------------------------------------------------

_STEP_HANDLERS: dict[str, Callable[..., dict[str, Any]]] = {
    "validate_sections": _step_validate_sections,
    "validate_committee": _step_validate_committee,
    "generate_package": _step_generate_package,
    "control_gaps": _step_control_gaps,
    "mark_ready": _step_mark_ready,
    "validate_registry": _step_validate_registry,
    "qa_readiness": _step_qa_readiness,
    "update_lifecycle": _step_update_lifecycle,
    "notify_shipped": _step_notify_shipped,
    "scan_registry": _step_scan_registry,
    "scan_errors": _step_scan_errors,
    "watchdog_status": _step_watchdog_status,
    "remediate_errors": _step_remediate_errors,
    "weekly_briefing": _step_weekly_briefing,
    "ops_snapshot": _step_ops_snapshot,
    "ceo_queue_reminder": _step_ceo_queue_reminder,
    "cost_snapshot": _step_cost_snapshot,
    "start_investigation": _step_start_investigation,
    "sync_product_kb": _step_sync_product_kb,
    "ingest_beta_feedback": _step_ingest_beta_feedback,
    "sav_ceo_pending": _step_sav_ceo_pending,
    "validate_registry_gaming": _step_validate_registry_gaming,
    "validate_registry_robotics": _step_validate_registry_robotics,
    "validate_gaming_readiness": _step_validate_gaming_readiness,
    "validate_robotics_readiness": _step_validate_robotics_readiness,
}


def _register_extension_recipes() -> None:
    """Load Phase 30 validation recipes without inlining them here (BUG-004)."""
    try:
        from services.workflow_validation_recipes import register_validation_recipes

        register_validation_recipes()
    except Exception as exc:
        logger.warning("validation recipes not loaded: %s", exc)


_register_extension_recipes()


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _apply_handler(
    handler: Callable[..., dict[str, Any]],
    ctx: dict[str, Any],
    prior_steps: list[StepRun],
) -> dict[str, Any]:
    """Invoke handler with prior_steps when the signature accepts it."""
    import inspect

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
