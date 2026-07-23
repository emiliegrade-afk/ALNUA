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

logger = logging.getLogger(__name__)

StepStatus = Literal["PENDING", "IN_PROGRESS", "OK", "A_VERIFIER", "ECART"]
RunStatus = Literal["running", "completed", "blocked", "failed"]

_RUNS_DIR = get_hub_repo_path() / "data" / "workflow_runs"

# Core dossier sections required before CEO package
_CEO_REQUIRED_SECTIONS = frozenset({"problem", "solution", "market", "mvp", "decision"})


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
# Step handlers — dossier_ceo
# ---------------------------------------------------------------------------

def _step_validate_sections(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.rnd_repository import get_rnd_repository

    dossier_id = ctx.get("dossier_id", "")
    if not dossier_id:
        return {"status": "ECART", "detail": "dossier_id requis", "gaps": ["contexte.dossier_id manquant"]}

    repo = get_rnd_repository()
    dossier = repo.get_dossier(dossier_id)
    if not dossier:
        return {"status": "ECART", "detail": "Dossier introuvable", "gaps": [f"dossier {dossier_id}"]}

    sections = dossier.sections or []
    by_key = {s.section_key: s for s in sections}
    missing = [k for k in _CEO_REQUIRED_SECTIONS if by_key.get(k, None) is None or by_key[k].status != "validated"]
    validated_count = sum(1 for s in sections if s.status == "validated")

    if len(missing) > 2:
        return {
            "status": "ECART",
            "detail": f"{validated_count}/{len(sections)} validées — manque {', '.join(missing)}",
            "gaps": [f"section.{k} non validée" for k in missing],
            "result": {"validated_count": validated_count, "missing": missing},
        }
    if missing:
        return {
            "status": "A_VERIFIER",
            "detail": f"Sections mineures à revoir : {', '.join(missing)}",
            "gaps": [f"section.{k}" for k in missing],
            "result": {"validated_count": validated_count, "missing": missing},
        }
    return {
        "status": "OK",
        "detail": f"{validated_count} sections validées (core OK)",
        "result": {"validated_count": validated_count},
    }


def _step_validate_committee(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.rnd_repository import get_rnd_repository

    dossier_id = ctx.get("dossier_id", "")
    dossier = get_rnd_repository().get_dossier(dossier_id)
    if not dossier:
        return {"status": "ECART", "detail": "Dossier introuvable", "gaps": ["dossier"]}

    cr = (dossier.committee_report_md or "").strip()
    if len(cr) < 40:
        return {
            "status": "ECART",
            "detail": "Compte-rendu comité absent ou trop court",
            "gaps": ["committee_report_md"],
        }
    if len(cr) < 200:
        return {
            "status": "A_VERIFIER",
            "detail": "CR comité présent mais court — à relire",
            "gaps": ["committee_report_md.short"],
            "result": {"cr_length": len(cr)},
        }
    return {"status": "OK", "detail": f"CR comité OK ({len(cr)} car.)", "result": {"cr_length": len(cr)}}


def _step_generate_package(ctx: dict[str, Any]) -> dict[str, Any]:
    from agents.rnd_ceo_agent import CeoPackageNotReadyError, RndCeoAgent

    dossier_id = ctx.get("dossier_id", "")
    force = bool(ctx.get("force", False))
    try:
        result = RndCeoAgent().generate_package(dossier_id, force=force)
        return {
            "status": "OK",
            "detail": "Package CEO généré" if result.get("regenerated", True) else "Package existant réutilisé",
            "result": {"regenerated": result.get("regenerated", True), "has_package": bool(result.get("package"))},
        }
    except CeoPackageNotReadyError as exc:
        return {"status": "ECART", "detail": str(exc), "gaps": ["ceo_package_not_ready"]}
    except Exception as exc:
        logger.exception("generate_package failed")
        return {"status": "ECART", "detail": str(exc), "gaps": ["generate_package_error"]}


def _step_control_gaps(ctx: dict[str, Any]) -> dict[str, Any]:
    from agents.rnd_ceo_agent import RndCeoAgent

    dossier_id = ctx.get("dossier_id", "")
    pkg_view = RndCeoAgent().get_package(dossier_id)
    pkg = pkg_view.get("package") or {}
    gaps: list[str] = []

    if not pkg:
        return {"status": "ECART", "detail": "Package CEO absent après génération", "gaps": ["package"]}

    rec = (pkg.get("recommendation") or "").strip()
    if rec not in ("GO", "MAYBE", "NO"):
        gaps.append("recommendation.missing")

    risks = pkg.get("risks") or pkg.get("top_risks") or []
    if not risks:
        gaps.append("risks.empty")

    finance = pkg.get("finance_summary") or pkg.get("finance") or {}
    if isinstance(finance, dict) and not any(finance.values()):
        gaps.append("finance_summary.empty")

    if "recommendation.missing" in gaps:
        return {
            "status": "ECART",
            "detail": "Recommandation GO/MAYBE/NO absente du package",
            "gaps": gaps,
        }
    if gaps:
        return {
            "status": "A_VERIFIER",
            "detail": f"Points à vérifier : {', '.join(gaps)}",
            "gaps": gaps,
            "result": {"recommendation": rec},
        }
    return {
        "status": "OK",
        "detail": f"Contrôle OK — recommandation {rec}",
        "result": {"recommendation": rec},
    }


def _step_mark_ready(ctx: dict[str, Any], prior_steps: list[StepRun]) -> dict[str, Any]:
    from services.rnd_repository import get_rnd_repository

    # Block if any prior step is ECART
    for step in prior_steps:
        if step.status == "ECART":
            return {"status": "ECART", "detail": f"Bloqué par étape {step.step_id}", "gaps": step.gaps}

    dossier_id = ctx.get("dossier_id", "")
    repo = get_rnd_repository()
    dossier = repo.get_dossier(dossier_id)
    if not dossier:
        return {"status": "ECART", "detail": "Dossier introuvable", "gaps": ["dossier"]}

    if dossier.status == "ready_for_ceo":
        return {"status": "OK", "detail": "Déjà ready_for_ceo", "result": {"status": dossier.status}}

    updated = repo.update_dossier(dossier_id, {"status": "ready_for_ceo"})
    if not updated:
        return {"status": "ECART", "detail": "Mise à jour statut échouée", "gaps": ["update_dossier"]}

    return {
        "status": "OK",
        "detail": "Dossier marqué ready_for_ceo — en attente décision Emilie",
        "result": {"status": "ready_for_ceo"},
    }


# ---------------------------------------------------------------------------
# Step handlers — ship_app
# ---------------------------------------------------------------------------

def _step_validate_registry(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.app_registry import get_app

    slug = (ctx.get("slug") or "").strip()
    if not slug:
        return {"status": "ECART", "detail": "slug requis", "gaps": ["context.slug"]}

    entry = get_app(slug)
    if not entry:
        return {"status": "ECART", "detail": f"App '{slug}' absente du registry", "gaps": ["registry.slug"]}
    if not entry.enabled:
        return {"status": "ECART", "detail": f"App '{slug}' désactivée", "gaps": ["registry.disabled"]}
    if not entry.path_exists:
        return {
            "status": "ECART",
            "detail": f"Chemin local introuvable : {entry.local_path}",
            "gaps": ["local_path.missing"],
            "result": entry.model_dump(),
        }
    return {
        "status": "OK",
        "detail": f"{entry.name} — path OK",
        "result": {"slug": slug, "branch": entry.branch, "local_path": entry.local_path},
    }


def _step_qa_readiness(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.company_errors import count_open_errors, list_open_errors

    slug = (ctx.get("slug") or "").strip()
    open_count = count_open_errors(repo_slug=slug)
    errors = list_open_errors(repo_slug=slug, limit=5)
    max_allowed = int(ctx.get("max_open_errors", 3))

    if open_count > max_allowed:
        return {
            "status": "ECART",
            "detail": f"{open_count} erreurs ouvertes (max {max_allowed})",
            "gaps": [f"coding_error.{e.get('id')}" for e in errors],
            "result": {"open_count": open_count, "sample": errors},
        }
    if open_count > 0:
        return {
            "status": "A_VERIFIER",
            "detail": f"{open_count} erreur(s) ouverte(s) — release possible avec vigilance",
            "gaps": [f"coding_error.{e.get('id')}" for e in errors],
            "result": {"open_count": open_count},
        }
    return {"status": "OK", "detail": "Aucune erreur coding ouverte", "result": {"open_count": 0}}


def _step_update_lifecycle(ctx: dict[str, Any], prior_steps: list[StepRun]) -> dict[str, Any]:
    from services.app_registry import AppRegistryUpsert, get_app, upsert_app

    for step in prior_steps:
        if step.status == "ECART":
            return {"status": "ECART", "detail": f"Bloqué par {step.step_id}", "gaps": step.gaps}

    slug = (ctx.get("slug") or "").strip()
    target = ctx.get("target_status", "beta")
    if target not in ("idea", "build", "beta", "prod"):
        target = "beta"

    entry = get_app(slug)
    if not entry:
        return {"status": "ECART", "detail": "App introuvable", "gaps": ["registry.slug"]}

    upsert_app(
        AppRegistryUpsert(
            slug=slug,
            name=entry.name,
            branch=entry.branch,
            github_repo=entry.github_repo,
            local_path=entry.local_path,
            description=entry.description,
            stack=entry.stack,
            prod_url=entry.prod_url or ctx.get("prod_url", ""),
            enabled=entry.enabled,
            lifecycle_status=target,
        )
    )
    return {
        "status": "OK",
        "detail": f"lifecycle_status → {target}",
        "result": {"slug": slug, "lifecycle_status": target},
    }


def _step_notify_shipped(ctx: dict[str, Any], prior_steps: list[StepRun]) -> dict[str, Any]:
    from services.event_bus import emit

    for step in prior_steps:
        if step.status == "ECART":
            return {"status": "ECART", "detail": f"Bloqué par {step.step_id}", "gaps": step.gaps}

    slug = (ctx.get("slug") or "").strip()
    target = ctx.get("target_status", "beta")
    try:
        emit(
            "feature_shipped",
            {"feature": f"Release {slug} ({target})", "slug": slug, "status": target},
            source_agent="workflow_engine",
        )
    except Exception as exc:
        logger.debug("feature_shipped emit failed: %s", exc)

    return {
        "status": "OK",
        "detail": f"Événement feature_shipped émis pour {slug}",
        "result": {"slug": slug, "target_status": target},
    }


# ---------------------------------------------------------------------------
# Step handlers — run_ops
# ---------------------------------------------------------------------------

def _step_scan_registry(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.app_registry import list_apps

    branch_filter = ctx.get("branch")
    apps = [a for a in list_apps(include_disabled=False) if a.slug != "hub"]
    if branch_filter:
        apps = [a for a in apps if a.branch == branch_filter]

    if not apps:
        return {"status": "ECART", "detail": "Aucune app active dans le registry", "gaps": ["registry.empty"]}

    return {
        "status": "OK",
        "detail": f"{len(apps)} app(s) surveillée(s)",
        "result": {
            "apps": [
                {
                    "slug": a.slug,
                    "name": a.name,
                    "branch": a.branch,
                    "path_exists": a.path_exists,
                    "lifecycle_status": getattr(a, "lifecycle_status", "build"),
                }
                for a in apps
            ]
        },
    }


def _step_scan_errors(ctx: dict[str, Any], prior_steps: list[StepRun]) -> dict[str, Any]:
    from services.company_errors import summarize_open_by_repo

    scan = next((s.result for s in prior_steps if s.step_id == "scan_registry"), None)
    apps = (scan or {}).get("apps") or []
    if not apps:
        return {"status": "ECART", "detail": "scan_registry requis", "gaps": ["scan_registry"]}

    per_repo = summarize_open_by_repo()
    total_open = sum(r["open_count"] for r in per_repo)

    status: StepStatus = "OK"
    if total_open > 10:
        status = "A_VERIFIER"
    detail = f"{total_open} erreur(s) ouverte(s) sur {len(apps)} repo(s)"
    if per_repo:
        detail += f" — actifs : {', '.join(r['slug'] for r in per_repo)}"

    return {
        "status": status,
        "detail": detail,
        "result": {"total_open": total_open, "repos_with_errors": per_repo},
        "gaps": [f"{r['slug']}:{r['open_count']}" for r in per_repo] if total_open > 10 else [],
    }


def _step_remediate_errors(ctx: dict[str, Any], prior_steps: list[StepRun]) -> dict[str, Any]:
    if not ctx.get("auto_remediate", True):
        return {"status": "OK", "detail": "Auto-remédiation désactivée", "result": {"skipped": True}}

    scan = next((s.result for s in prior_steps if s.step_id == "scan_errors"), None)
    total_open = (scan or {}).get("total_open") or 0
    if total_open < 1:
        return {"status": "OK", "detail": "Aucune erreur — rien à remédier", "result": {"count": 0}}

    from services.company_errors import auto_create_fix_issues

    outcome = auto_create_fix_issues(max_issues=int(ctx.get("max_auto_issues", 5)))
    created = outcome.get("created") or []
    if not created and outcome.get("error"):
        return {
            "status": "A_VERIFIER",
            "detail": outcome.get("error", "auto-issues échoué"),
            "result": outcome,
        }
    return {
        "status": "OK",
        "detail": f"{len(created)} issue(s) agent-ready créée(s)",
        "result": outcome,
    }


def _step_weekly_briefing(ctx: dict[str, Any]) -> dict[str, Any]:
    try:
        from services.daily_briefing import run_quick_briefing

        brief = run_quick_briefing()
        headline = brief.get("headline") or brief.get("summary") or "Brief généré"
        return {"status": "OK", "detail": str(headline)[:200], "result": brief}
    except Exception as exc:
        return {"status": "A_VERIFIER", "detail": str(exc)[:200], "gaps": ["briefing"]}


def _step_ops_snapshot(ctx: dict[str, Any], prior_steps: list[StepRun]) -> dict[str, Any]:
    from services.company_errors import summarize_open_by_repo
    from services.run_watchdog_registry import build_watchdog_coverage_report

    per_repo = summarize_open_by_repo()
    total = sum(r["open_count"] for r in per_repo)
    wd = build_watchdog_coverage_report()
    detail = f"{total} erreur(s) · {wd.get('summary', '')}"
    return {
        "status": "A_VERIFIER" if total > 5 else "OK",
        "detail": detail,
        "result": {"total_open": total, "repos": per_repo, "watchdog": wd},
    }


def _step_ceo_queue_reminder(ctx: dict[str, Any]) -> dict[str, Any]:
    try:
        from agents.rnd_ceo_agent import RndCeoAgent

        queue = RndCeoAgent().list_ceo_queue(limit=10)
        to_validate = queue.get("to_validate") or []
        to_prepare = queue.get("to_prepare") or []
        if not to_validate and not to_prepare:
            return {
                "status": "OK",
                "detail": "Aucun dossier en attente — ta validation produit n'est pas requise",
                "result": queue,
            }
        titles = [d.get("title", "?")[:40] for d in to_validate[:3]]
        detail = (
            f"{len(to_validate)} à valider, {len(to_prepare)} à préparer"
            + (f" — ex: {', '.join(titles)}" if titles else "")
        )
        return {
            "status": "A_VERIFIER",
            "detail": detail + " (decision CEO requise)",
            "result": queue,
            "gaps": ["ceo.validation_pending"],
        }
    except Exception as exc:
        return {"status": "A_VERIFIER", "detail": str(exc)[:200], "gaps": ["ceo_queue"]}


def _step_cost_snapshot(ctx: dict[str, Any]) -> dict[str, Any]:
    try:
        from services.cost_monitor import check_budget_alert, get_cost_report

        report = get_cost_report(days=7)
        alert = check_budget_alert(daily_budget_usd=float(ctx.get("daily_budget_usd", 10.0)))
        total = report.get("total_usd") or report.get("total_cost_usd") or 0
        severity = alert.get("severity", "ok")
        status: StepStatus = "OK" if severity == "ok" else "A_VERIFIER"
        return {
            "status": status,
            "detail": f"7j : ${total:.2f} USD · alerte {severity}",
            "result": {"report": report, "alert": alert},
        }
    except Exception as exc:
        return {"status": "A_VERIFIER", "detail": str(exc)[:120], "gaps": ["cost"]}


def _step_watchdog_status(ctx: dict[str, Any], prior_steps: list[StepRun]) -> dict[str, Any]:
    from services.run_watchdog_registry import build_watchdog_coverage_report

    report = build_watchdog_coverage_report()
    unmapped = report.get("unmapped_slugs") or []
    gaps = [f"watchdog.unmapped.{s}" for s in unmapped]

    status: StepStatus = "OK"
    if unmapped:
        status = "A_VERIFIER"

    return {
        "status": status,
        "detail": report.get("summary", ""),
        "result": report,
        "gaps": gaps,
    }


# ---------------------------------------------------------------------------
# Step handlers — explore
# ---------------------------------------------------------------------------

def _step_start_investigation(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.rnd_hypothesis_tree import start_investigation

    topic = (ctx.get("topic") or ctx.get("query") or "").strip()
    if not topic:
        return {"status": "ECART", "detail": "topic requis", "gaps": ["context.topic"]}

    result = start_investigation(topic, requested_by=ctx.get("requested_by", "workflow_engine"))
    if not result.get("success"):
        return {"status": "ECART", "detail": result.get("error", "échec"), "gaps": ["investigation"]}
    return {
        "status": "OK",
        "detail": f"Arbre lancé : {result.get('slug')}",
        "result": result,
    }


# ---------------------------------------------------------------------------
# Step handlers — sav_lite
# ---------------------------------------------------------------------------

def _step_sync_product_kb(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.product_kb import sync_kb_from_registry

    outcome = sync_kb_from_registry(only_prod_beta=bool(ctx.get("only_prod_beta", False)))
    synced = outcome.get("synced", 0)
    if synced < 1:
        return {
            "status": "A_VERIFIER",
            "detail": "Aucun produit synchronisé dans product_kb",
            "gaps": ["product_kb.empty"],
            "result": outcome,
        }
    return {
        "status": "OK",
        "detail": f"{synced} fiche(s) KB synchronisée(s)",
        "result": outcome,
    }


def _step_ingest_beta_feedback(ctx: dict[str, Any]) -> dict[str, Any]:
    if ctx.get("skip_beta_ingest"):
        return {"status": "OK", "detail": "Ingest beta ignoré", "result": {"skipped": True}}

    from services.sav_lite import ingest_recent_beta_feedback

    outcome = ingest_recent_beta_feedback(
        days=int(ctx.get("beta_days", 7)),
        limit=int(ctx.get("beta_limit", 10)),
    )
    ingested = outcome.get("ingested", 0)
    if outcome.get("error"):
        return {
            "status": "A_VERIFIER",
            "detail": outcome.get("error", "ingest beta échoué"),
            "result": outcome,
            "gaps": ["beta_ingest"],
        }
    return {
        "status": "OK" if ingested >= 0 else "A_VERIFIER",
        "detail": f"{ingested} cas SAV créé(s) depuis le feedback beta",
        "result": outcome,
    }


def _step_sav_ceo_pending(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.sav_lite import list_sav_cases

    pending = list_sav_cases(status="awaiting_ceo", needs_ceo=True, limit=20)
    draft_ready = list_sav_cases(status="draft_ready", limit=20)

    if not pending and not draft_ready:
        return {
            "status": "OK",
            "detail": "Aucun cas SAV en attente",
            "result": {"awaiting_ceo": 0, "draft_ready": 0},
        }

    subjects = [c.get("subject", "?")[:40] for c in pending[:3]]
    detail = f"{len(pending)} validation CEO · {len(draft_ready)} brouillon(s) prêt(s)"
    if subjects:
        detail += f" — ex: {', '.join(subjects)}"

    status: StepStatus = "A_VERIFIER" if pending else "OK"
    gaps = ["sav.ceo_validation"] if pending else []

    if pending and ctx.get("notify_ceo", True):
        try:
            from skills.skill_telegram_notify import notify_telegram

            notify_telegram(
                f"📋 SAV — {len(pending)} cas à valider sur /secretary\n"
                + "\n".join(f"• {s}" for s in subjects[:5])
            )
        except Exception:
            pass

    return {
        "status": status,
        "detail": detail,
        "result": {"awaiting_ceo": len(pending), "draft_ready": len(draft_ready), "pending": pending[:5]},
        "gaps": gaps,
    }


def _step_validate_registry_gaming(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.ship_readiness import validate_registry_for_branch

    slug = (ctx.get("slug") or "").strip()
    return validate_registry_for_branch(slug, required_branch="gaming")


def _step_validate_registry_robotics(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.ship_readiness import validate_registry_for_branch

    slug = (ctx.get("slug") or "").strip()
    return validate_registry_for_branch(slug, required_branch="robotics")


def _step_validate_gaming_readiness(ctx: dict[str, Any], prior_steps: list[StepRun]) -> dict[str, Any]:
    from services.app_registry import get_app
    from services.ship_readiness import check_gaming_readiness

    for step in prior_steps:
        if step.status == "ECART":
            return {"status": "ECART", "detail": f"Bloqué par {step.step_id}", "gaps": step.gaps}

    slug = (ctx.get("slug") or "").strip()
    entry = get_app(slug)
    if not entry:
        return {"status": "ECART", "detail": "Registry requis", "gaps": ["registry.slug"]}

    report = check_gaming_readiness(entry.local_path, slug=slug)
    if not report.get("ready"):
        return {
            "status": "ECART",
            "detail": report.get("detail", "Gaming readiness ECART"),
            "gaps": report.get("gaps") or ["gaming.readiness"],
            "result": report,
        }
    if report.get("soft") or report.get("gaps"):
        return {
            "status": "A_VERIFIER",
            "detail": report.get("detail", "Points gaming à valider"),
            "gaps": report.get("gaps") or [],
            "result": report,
        }
    return {
        "status": "OK",
        "detail": report.get("detail", "Gaming readiness OK"),
        "result": report,
    }


def _step_validate_robotics_readiness(ctx: dict[str, Any], prior_steps: list[StepRun]) -> dict[str, Any]:
    from services.app_registry import get_app
    from services.ship_readiness import check_robotics_readiness

    for step in prior_steps:
        if step.status == "ECART":
            return {"status": "ECART", "detail": f"Bloqué par {step.step_id}", "gaps": step.gaps}

    slug = (ctx.get("slug") or "").strip()
    entry = get_app(slug)
    if not entry:
        return {"status": "ECART", "detail": "Registry requis", "gaps": ["registry.slug"]}

    report = check_robotics_readiness(entry.local_path, slug=slug)
    if not report.get("ready"):
        return {
            "status": "ECART",
            "detail": report.get("detail", "Robotics readiness ECART"),
            "gaps": report.get("gaps") or ["robotics.readiness"],
            "result": report,
        }
    if report.get("soft") or report.get("gaps"):
        return {
            "status": "A_VERIFIER",
            "detail": report.get("detail", "Points robotics à valider"),
            "gaps": report.get("gaps") or [],
            "result": report,
        }
    return {
        "status": "OK",
        "detail": report.get("detail", "Robotics readiness OK"),
        "result": report,
    }


# Handler registry
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
