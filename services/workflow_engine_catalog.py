"""Workflow engine — recipe catalogue."""

from __future__ import annotations

from typing import Any

from services.workflow_engine_models import WorkflowRecipe, WorkflowStepDef

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
    WorkflowRecipe(
        id="mission_ship",
        name="Mission ship — Review Chain + integrate",
        description=(
            "QA readiness → Review Chain (auto/board/policy/integrate) → "
            "lifecycle → notify. dry_run=true par défaut dans le contexte."
        ),
        head_agent="dev_integrator",
        priority="P1",
        steps=[
            WorkflowStepDef(id="qa_readiness", label="Erreurs coding ouvertes", head_agent="qa"),
            WorkflowStepDef(id="review_chain", label="Review Chain ordonnée", head_agent="dev_integrator"),
            WorkflowStepDef(id="require_integrate", label="Integrate si N>1 branches", head_agent="dev_integrator"),
            WorkflowStepDef(id="update_lifecycle", label="Mise à jour lifecycle", head_agent="coo"),
            WorkflowStepDef(id="notify_shipped", label="Événement feature_shipped", head_agent="coo"),
        ],
    ),
]


def list_recipes() -> list[dict[str, Any]]:
    return [r.model_dump() for r in RECIPE_CATALOG]


def get_recipe(recipe_id: str) -> WorkflowRecipe | None:
    return next((r for r in RECIPE_CATALOG if r.id == recipe_id), None)
