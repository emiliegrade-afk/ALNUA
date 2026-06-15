"""PRD Engineering pipeline — spec generation + GitHub issue factory (Phase 3)."""

from __future__ import annotations

import logging
from typing import Any

from agents.base import log_agent_action
from database.supabase_client import get_supabase
from services.engineering_spec import (
    EngineeringSpecResult,
    append_engineering_spec_to_package,
    generate_engineering_spec,
)
from services.prd_issues import publish_tasks_to_github, read_build_manifest
from services.rnd_repository import get_rnd_repository
from services.rnd_schemas import RndDossierOut

logger = logging.getLogger(__name__)

CEO_APPROVED_STATUSES = frozenset({"ceo_approved", "in_conception"})


class PrdEngineeringNotReadyError(ValueError):
    """Dossier not eligible for PRD engineering."""


def _load_dossier(dossier_id: str) -> RndDossierOut:
    repo = get_rnd_repository(get_supabase())
    dossier = repo.get_dossier(dossier_id)
    if not dossier:
        raise ValueError(f"Dossier {dossier_id} introuvable")
    return dossier


def _persist_ceo_package(dossier_id: str, package: dict[str, Any]) -> None:
    repo = get_rnd_repository(get_supabase())
    repo.update_dossier(dossier_id, {"ceo_package_json": package})


def run_engineering_spec_generation(
    dossier_id: str,
    *,
    force: bool = False,
    debate_rounds: int = 1,
    refine_with_pm: bool = True,
) -> dict[str, Any]:
    """
    Generate §10 Product Engineering Spec and merge into ceo_package_json.
    Requires CEO package (blocks 1-9) unless force on approved dossier.
    """
    dossier = _load_dossier(dossier_id)
    package = dict(dossier.ceo_package_json or {})

    if not package and dossier.status not in CEO_APPROVED_STATUSES:
        raise PrdEngineeringNotReadyError(
            "Générer d'abord le dossier CEO (sections 1-9)"
        )

    existing = package.get("engineering_spec")
    if existing and not force:
        return {
            "message": "Engineering spec déjà présente — passer force=true pour regénérer",
            "engineering_spec": existing,
            "task_count": len((existing.get("task_breakdown") or [])),
            "skipped": True,
        }

    spec = generate_engineering_spec(
        dossier,
        ceo_package=package,
        debate_rounds=debate_rounds,
        refine_with_pm=refine_with_pm,
    )
    updated = append_engineering_spec_to_package(package, spec)
    _persist_ceo_package(dossier_id, updated)

    try:
        log_agent_action(
            get_supabase(),
            "spec_agent",
            "generate_engineering_spec",
            input_summary=dossier.slug,
            output_summary=f"tasks={len(spec.task_breakdown)}",
        )
    except Exception:
        pass

    return {
        "message": f"Engineering spec générée — {len(spec.task_breakdown)} tâches",
        "engineering_spec": spec.to_dict(),
        "task_count": len(spec.task_breakdown),
        "qa_verdict": spec.qa_verdict,
        "ceo_package_updated": True,
    }


def run_prd_decompose(
    dossier_id: str,
    *,
    repo_slug: str | None = None,
    dry_run: bool = False,
    mark_ready_count: int = 3,
    force_spec: bool = False,
    debate_rounds: int = 1,
) -> dict[str, Any]:
    """
    Full Phase 3 pipeline: engineering spec (if missing) → GitHub issues + build manifest.
    CEO approval required unless dry_run.
    """
    dossier = _load_dossier(dossier_id)

    if dossier.ceo_status != "approved" and not dry_run:
        raise PrdEngineeringNotReadyError(
            "Validation CEO requise (ceo_status=approved) avant publication des issues"
        )

    package = dict(dossier.ceo_package_json or {})
    eng = package.get("engineering_spec")

    if not eng or force_spec:
        gen = run_engineering_spec_generation(
            dossier_id,
            force=force_spec or not eng,
            debate_rounds=debate_rounds,
        )
        if not gen.get("skipped"):
            dossier = _load_dossier(dossier_id)
            package = dict(dossier.ceo_package_json or {})
            eng = package.get("engineering_spec")

    if not eng:
        raise PrdEngineeringNotReadyError("Engineering spec absente après génération")

    from services.engineering_spec import EngineeringTask

    tasks = [
        EngineeringTask.model_validate(t)
        for t in (eng.get("task_breakdown") or [])
        if isinstance(t, dict)
    ]
    if not tasks:
        raise PrdEngineeringNotReadyError("task_breakdown vide — regénérer la spec")

    publish = publish_tasks_to_github(
        dossier,
        tasks,
        repo_slug=repo_slug,
        dry_run=dry_run,
        mark_ready_count=mark_ready_count,
        extra_context=f"Source: CEO dossier {dossier.slug}",
    )

    try:
        log_agent_action(
            get_supabase(),
            "pm_agent",
            "decompose_prd_to_github_issues",
            input_summary=dossier.slug,
            output_summary=f"created={publish['created_count']}",
        )
    except Exception:
        pass

    return {
        "message": (
            f"PRD décomposé — {publish['created_count']} issues créées, "
            f"{publish['skipped_count']} ignorées (doublons)"
        ),
        "dossier_id": dossier_id,
        "dossier_slug": dossier.slug,
        "dry_run": dry_run,
        **publish,
    }


def get_build_status(dossier_id: str) -> dict[str, Any]:
    dossier = _load_dossier(dossier_id)
    manifest = read_build_manifest(dossier.slug)
    package = dossier.ceo_package_json or {}
    eng = package.get("engineering_spec") or {}
    return {
        "dossier_id": dossier_id,
        "slug": dossier.slug,
        "ceo_status": dossier.ceo_status,
        "has_engineering_spec": bool(eng),
        "task_count": len(eng.get("task_breakdown") or []),
        "build_manifest": manifest,
        "build_manifest_path": manifest.get("github_repo") and f"{dossier.slug}.build.json",
    }
