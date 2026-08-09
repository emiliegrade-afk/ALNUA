"""R&D routes — peeled from rnd.py (debt paydown)."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()

@router.post("/rnd/dossiers")
def rnd_create_dossier(
    body: dict[str, Any],
    auto_enrich: bool = Query(
        default=True,
        alias="enrich",
        description="Enrichir sections + finance en arrière-plan",
    ),
) -> dict[str, Any]:
    """Créer un dossier R&D à partir d'une idée (équivalent promote, body JSON)."""
    import threading

    from agents.rnd_dossier_agent import RndDossierAgent
    from services.rnd_schemas import RndDossierCreateBody

    payload = RndDossierCreateBody.model_validate(body)
    agent = RndDossierAgent()
    try:
        result = agent.create_dossier(payload.idea_id, actor="emilie", enrich=False)
        dossier_id = result["dossier"]["id"]

        if auto_enrich:

            def _enrich_bg() -> None:
                try:
                    agent.enrich_dossier(dossier_id, actor="rnd_dossier_agent")
                except Exception:
                    logger.exception("rnd_enrich_background failed for %s", dossier_id)

            threading.Thread(target=_enrich_bg, daemon=True).start()
            result["enriching"] = True
            result["message"] = (
                f"Dossier R&D « {result['dossier']['title']} » créé — "
                f"enrichissement sections + business case en cours (30–60 s)."
            )
        else:
            result["enriching"] = False
            result["message"] = (
                f"Dossier R&D « {result['dossier']['title']} » créé — "
                f"{result['dossier']['sections_total_count']} sections squelette."
            )
        return result
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_create_dossier failed for %s", payload.idea_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/rnd/dossiers")
def rnd_list_dossiers(
    status: str | None = Query(default=None),
    domain: str | None = Query(default=None),
    limit: int = Query(default=50, le=100),
    ceo_queue: bool = Query(default=False, description="Inclure file CEO (to_validate/to_prepare)"),
) -> list[dict[str, Any]] | dict[str, Any]:
    from agents.rnd_dossier_agent import RndDossierAgent
    from agents.rnd_ceo_agent import RndCeoAgent

    if ceo_queue:
        return RndCeoAgent().list_ceo_queue(limit=limit)
    return RndDossierAgent().list_dossiers(status=status, domain=domain, limit=limit)


@router.get("/rnd/dossiers/slug/{slug}")
def rnd_get_dossier_by_slug(slug: str) -> dict[str, Any]:
    from agents.rnd_dossier_agent import RndDossierAgent

    dossier = RndDossierAgent().get_dossier(slug)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    return dossier.model_dump()


@router.get("/rnd/dossiers/table-view")
def rnd_dossiers_table_view(
    status: str | None = Query(default=None),
    domain: str | None = Query(default=None),
    limit: int = Query(default=50, le=100),
) -> list[dict[str, Any]]:
    """Vue table Dossiers (Phase 27) — préjoint idée/vote Conseil/documents/
    section marché par dossier, pour éviter un N+1 côté frontend."""
    from services.rnd_dossier_table import build_dossier_table_rows

    try:
        return build_dossier_table_rows(status=status, domain=domain, limit=limit)
    except Exception as exc:
        logger.exception("rnd_dossiers_table_view failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/rnd/dossiers/{dossier_id}")
def rnd_get_dossier(dossier_id: str) -> dict[str, Any]:
    from agents.rnd_dossier_agent import RndDossierAgent

    dossier = RndDossierAgent().get_dossier(dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    return dossier.model_dump()


@router.patch("/rnd/dossiers/{dossier_id}")
def rnd_patch_dossier(dossier_id: str, body: dict[str, Any]) -> dict[str, Any]:
    from services.rnd_repository import get_rnd_repository
    from services.rnd_schemas import RndDossierPatchBody

    allowed = RndDossierPatchBody.model_validate(body)
    values = allowed.model_dump(exclude_none=True)
    if not values:
        raise HTTPException(status_code=400, detail="Aucun champ à mettre à jour")
    dossier = get_rnd_repository().update_dossier(dossier_id, values)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    return dossier.model_dump()


@router.get("/rnd/dossiers/{dossier_id}/events")
def rnd_get_dossier_events(
    dossier_id: str,
    limit: int = Query(default=50, le=200),
) -> list[dict[str, Any]]:
    from services.rnd_repository import get_rnd_repository

    events = get_rnd_repository().get_dossier_events(dossier_id, limit=limit)
    return [e.model_dump() for e in events]


@router.patch("/rnd/dossiers/{dossier_id}/sections/{section_key}")
def rnd_update_section(
    dossier_id: str,
    section_key: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    """Met à jour le contenu markdown d'une section (édition manuelle Emilie)."""
    from agents.rnd_dossier_agent import RndDossierAgent
    from services.rnd_schemas import RndSectionUpdateBody

    req = RndSectionUpdateBody.model_validate(body)
    try:
        dossier = RndDossierAgent().update_section(
            dossier_id,
            section_key,
            req.content_md,
            actor="emilie",
        )
        return dossier.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_update_section failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/enrich")
def rnd_enrich_dossier(dossier_id: str) -> dict[str, Any]:
    """Regénère sections LLM + business case pour un dossier existant."""
    from agents.rnd_dossier_agent import RndDossierAgent

    try:
        dossier = RndDossierAgent().enrich_dossier(dossier_id)
        return {"dossier": dossier.model_dump(), "message": "Dossier enrichi."}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_enrich_dossier failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/validate-section")
def rnd_validate_section(dossier_id: str, body: dict[str, Any]) -> dict[str, Any]:
    from agents.rnd_dossier_agent import RndDossierAgent
    from services.rnd_schemas import RndSectionActionBody

    req = RndSectionActionBody.model_validate(body)
    try:
        dossier = RndDossierAgent().validate_section(
            dossier_id, req.section_key, note=req.note
        )
        return dossier.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/request-revision")
def rnd_request_revision(dossier_id: str, body: dict[str, Any]) -> dict[str, Any]:
    from agents.rnd_dossier_agent import RndDossierAgent
    from services.rnd_schemas import RndSectionRevisionBody

    req = RndSectionRevisionBody.model_validate(body)
    try:
        dossier = RndDossierAgent().request_section_revision(
            dossier_id, req.section_key, req.revision_note
        )
        return dossier.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/regenerate-section")
def rnd_regenerate_section(dossier_id: str, body: dict[str, Any]) -> dict[str, Any]:
    from agents.rnd_dossier_agent import RndDossierAgent
    from services.rnd_schemas import RndSectionRevisionBody

    req = RndSectionRevisionBody.model_validate(body)
    try:
        dossier = RndDossierAgent().regenerate_section(
            dossier_id,
            req.section_key,
            revision_note=req.revision_note,
        )
        return dossier.model_dump()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.get("/rnd/dossiers/{dossier_id}/finance")
def rnd_get_finance(dossier_id: str) -> dict[str, Any]:
    from agents.rnd_dossier_agent import RndDossierAgent

    dossier = RndDossierAgent().get_dossier(dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    return {
        "finance_json": dossier.finance_json,
        "business_case": next(
            (s.content_md for s in dossier.sections if s.section_key == "business_case"),
            None,
        ),
    }


@router.post("/rnd/dossiers/{dossier_id}/finance/estimate")
def rnd_estimate_finance(dossier_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    from agents.rnd_dossier_agent import RndDossierAgent
    from services.rnd_schemas import RndFinanceReviseBody

    constraint = None
    if body:
        constraint = RndFinanceReviseBody.model_validate(body).constraint
    try:
        return RndDossierAgent().estimate_finance(dossier_id, constraint=constraint)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/rnd/health")
def rnd_module_health_endpoint() -> dict[str, Any]:
    from database.supabase_client import get_supabase
    from services.rnd_pipeline import rnd_module_health

    return rnd_module_health(get_supabase())


@router.get("/rnd/dossiers/{dossier_id}/pipeline")
def rnd_dossier_pipeline(dossier_id: str) -> dict[str, Any]:
    from services.rnd_pipeline import build_dossier_pipeline
    from services.rnd_repository import get_rnd_repository

    dossier = get_rnd_repository().get_dossier(dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    return build_dossier_pipeline(dossier)

