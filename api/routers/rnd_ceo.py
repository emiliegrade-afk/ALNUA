"""R&D routes — peeled from rnd.py (debt paydown)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()

@router.get("/rnd/ceo/pending-dossiers")
def rnd_ceo_pending_dossiers(
    limit: int = Query(default=20, le=50),
) -> list[dict[str, Any]]:
    """Dossiers R&D avec package CEO généré, en attente de validation Emilie."""
    from agents.rnd_ceo_agent import RndCeoAgent

    return RndCeoAgent().list_pending_dossiers(limit=limit)


@router.get("/rnd/ceo/queue")
def rnd_ceo_queue(
    limit: int = Query(default=20, le=50),
) -> dict[str, Any]:
    """File CEO : à valider (package prêt) + à finaliser (générer package)."""
    from agents.rnd_ceo_agent import RndCeoAgent

    return RndCeoAgent().list_ceo_queue(limit=limit)


@router.get("/rnd/dossiers/{dossier_id}/ceo/package")
def rnd_ceo_get_package(dossier_id: str) -> dict[str, Any]:
    from agents.rnd_ceo_agent import RndCeoAgent

    try:
        return RndCeoAgent().get_package(dossier_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/ceo/generate")
def rnd_ceo_generate_package(
    dossier_id: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from agents.rnd_ceo_agent import CeoPackageNotReadyError, RndCeoAgent
    from services.rnd_schemas import RndCeoGenerateBody

    payload = RndCeoGenerateBody.model_validate(body or {})
    try:
        return RndCeoAgent().generate_package(dossier_id, force=payload.force)
    except CeoPackageNotReadyError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_ceo_generate_package failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/ceo/decide")
def rnd_ceo_decide(
    dossier_id: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    from agents.rnd_ceo_agent import CeoDecisionError, RndCeoAgent
    from services.rnd_schemas import RndCeoDecisionBody

    payload = RndCeoDecisionBody.model_validate(body)
    if payload.ceo_status == "pending":
        raise HTTPException(status_code=400, detail="ceo_status must be approved, rejected, or pivot_requested")
    try:
        return RndCeoAgent().record_ceo_decision(
            dossier_id,
            ceo_status=payload.ceo_status,
            ceo_note=payload.ceo_note,
        )
    except CeoDecisionError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_ceo_decide failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/ceo/dispatch")
def rnd_ceo_dispatch(dossier_id: str) -> dict[str, Any]:
    from agents.rnd_ceo_agent import DispatchNotAllowedError, RndCeoAgent

    try:
        return RndCeoAgent().dispatch_to_coo(dossier_id)
    except DispatchNotAllowedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_ceo_dispatch failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/engineering-spec/generate")
def rnd_generate_engineering_spec(
    dossier_id: str,
    body: EngineeringSpecGenerateRequest | None = None,
) -> dict[str, Any]:
    """CEO package §10 — Léon (spec) + QA adversarial + PM refine."""
    from services.prd_engineering import (
        PrdEngineeringNotReadyError,
        run_engineering_spec_generation,
    )

    payload = body or EngineeringSpecGenerateRequest()
    try:
        return run_engineering_spec_generation(
            dossier_id,
            force=payload.force,
            debate_rounds=payload.debate_rounds,
            refine_with_pm=payload.refine_with_pm,
        )
    except PrdEngineeringNotReadyError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_generate_engineering_spec failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/engineering-spec/decompose")
def rnd_decompose_prd(
    dossier_id: str,
    body: PrdDecomposeRequest | None = None,
) -> dict[str, Any]:
    """PM → GitHub issues agent-ready + build manifest."""
    from services.prd_engineering import PrdEngineeringNotReadyError, run_prd_decompose

    payload = body or PrdDecomposeRequest()
    try:
        return run_prd_decompose(
            dossier_id,
            repo_slug=payload.repo_slug,
            dry_run=payload.dry_run,
            mark_ready_count=payload.mark_ready_count,
            force_spec=payload.force_spec,
            debate_rounds=payload.debate_rounds,
        )
    except PrdEngineeringNotReadyError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_decompose_prd failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/rnd/dossiers/{dossier_id}/build-manifest")
def rnd_build_manifest(dossier_id: str) -> dict[str, Any]:
    from services.prd_engineering import get_build_status

    try:
        return get_build_status(dossier_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/ceo/execute")
def rnd_ceo_execute_agents(dossier_id: str) -> dict[str, Any]:
    """Lance (ou relance) l'exécution réelle des agents après dispatch CEO."""
    from agents.rnd_ceo_agent import DispatchNotAllowedError, RndCeoAgent

    try:
        return RndCeoAgent().kickoff_execution(dossier_id)
    except DispatchNotAllowedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_ceo_execute failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


