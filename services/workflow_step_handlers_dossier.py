"""Workflow step handlers — dossier_ceo recipe (BUG-004 split)."""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Core dossier sections required before CEO package
_CEO_REQUIRED_SECTIONS = frozenset({"problem", "solution", "market", "mvp", "decision"})


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


def _step_mark_ready(ctx: dict[str, Any], prior_steps: list[Any]) -> dict[str, Any]:
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
