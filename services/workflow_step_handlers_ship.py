"""Workflow step handlers — ship_app/hub/game/robo recipes (BUG-004 split)."""

from __future__ import annotations

import logging
from typing import Any, Literal

logger = logging.getLogger(__name__)

StepStatus = Literal["PENDING", "IN_PROGRESS", "OK", "A_VERIFIER", "ECART"]


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


def _step_update_lifecycle(ctx: dict[str, Any], prior_steps: list[Any]) -> dict[str, Any]:
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


def _step_notify_shipped(ctx: dict[str, Any], prior_steps: list[Any]) -> dict[str, Any]:
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


def _step_validate_registry_gaming(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.ship_readiness import validate_registry_for_branch

    slug = (ctx.get("slug") or "").strip()
    return validate_registry_for_branch(slug, required_branch="gaming")


def _step_validate_registry_robotics(ctx: dict[str, Any]) -> dict[str, Any]:
    from services.ship_readiness import validate_registry_for_branch

    slug = (ctx.get("slug") or "").strip()
    return validate_registry_for_branch(slug, required_branch="robotics")


def _step_validate_gaming_readiness(ctx: dict[str, Any], prior_steps: list[Any]) -> dict[str, Any]:
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


def _step_validate_robotics_readiness(ctx: dict[str, Any], prior_steps: list[Any]) -> dict[str, Any]:
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
