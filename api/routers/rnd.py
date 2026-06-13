"""Auto-split from api/main.py — rnd routes."""

from __future__ import annotations

from api.route_common import *  # noqa: F403

router = APIRouter()



class RndInjectBody(BaseModel):
    idea: str
    source: str = "Emilie"

class RndVisionBody(BaseModel):
    vision: str


@router.get("/rnd/ideas")
def rnd_get_ideas(limit: int = Query(default=20, le=100), verdict: str | None = None) -> list[dict]:
    """Retourne les idées générées par le Centre R&D, triées par score."""
    try:
        from agents.rnd_center import get_top_ideas
        return get_top_ideas(limit=limit, verdict=verdict)
    except Exception as exc:
        logger.exception("rnd_get_ideas failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/rnd/vision")
def rnd_get_vision() -> dict[str, str]:
    """Retourne le fil conducteur R&D actuel."""
    try:
        from agents.rnd_center import get_vision
        return {"vision": get_vision()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/rnd/vision")
def rnd_set_vision(body: RndVisionBody) -> dict[str, str]:
    """Met à jour le fil conducteur R&D."""
    try:
        from agents.rnd_center import set_vision
        set_vision(body.vision)
        return {"ok": "vision mise à jour"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/rnd/inject")
def rnd_inject_idea(body: RndInjectBody) -> dict:
    """Injecte une idée d'Emilie dans le pipeline R&D (sera scorée au prochain cycle)."""
    try:
        from agents.rnd_center import inject_idea
        return inject_idea(body.idea, body.source)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/rnd/cycle")
def rnd_trigger_cycle() -> dict[str, str]:
    """Lance manuellement un cycle R&D complet (async)."""
    try:
        from agents.rnd_center import run_rnd_cycle
        import threading
        threading.Thread(target=lambda: run_rnd_cycle(blocking=True), daemon=True).start()
        return {"status": "Cycle R&D lancé en arrière-plan. Résultats disponibles dans quelques minutes."}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/rnd/competitive")
def rnd_get_competitive() -> list[dict]:
    """Retourne les analyses concurrentielles disponibles."""
    from pathlib import Path

    comp_dir = data_dir("rnd_competitive")
    results: list[dict] = []
    if not comp_dir.exists():
        return results

    for path in sorted(comp_dir.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
        try:
            text = path.read_text(encoding="utf-8")
            results.append({
                "product": path.stem.replace("_competitor_analysis", ""),
                "timestamp": path.stem.split("_")[0] if "_" in path.stem else path.stem,
                "analysis": text[:4000],
            })
        except Exception:
            pass

    for path in sorted(comp_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:10]:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                results.append(data)
        except Exception:
            pass

    return results




@router.get("/rnd/ideas/{idea_id}")
def rnd_get_idea(idea_id: str) -> dict[str, Any]:
    """Retourne une idée R&D par legacy_id ou UUID."""
    from agents.rnd_center import get_idea_by_id

    idea = get_idea_by_id(idea_id)
    if not idea:
        raise HTTPException(status_code=404, detail=f"Idée introuvable : {idea_id}")
    return idea


@router.post("/rnd/ideas/{idea_id}/promote")
def rnd_promote_idea(
    idea_id: str,
    auto_enrich: bool = Query(
        default=True,
        alias="enrich",
        description="Enrichir sections + finance en arrière-plan",
    ),
) -> dict[str, Any]:
    """Promouvoir une idée en dossier R&D (squelette rapide, enrichissement async)."""
    import threading

    from agents.rnd_dossier_agent import RndDossierAgent, promote_idea_to_dossier

    try:
        result = promote_idea_to_dossier(idea_id, actor="emilie", enrich=False)
        dossier_id = result["dossier"]["id"]

        if auto_enrich:

            def _enrich_bg() -> None:
                try:
                    RndDossierAgent().enrich_dossier(dossier_id, actor="rnd_dossier_agent")
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
        logger.exception("rnd_promote_idea failed for %s", idea_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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
) -> list[dict[str, Any]]:
    from agents.rnd_dossier_agent import RndDossierAgent

    return RndDossierAgent().list_dossiers(status=status, domain=domain, limit=limit)


@router.get("/rnd/dossiers/slug/{slug}")
def rnd_get_dossier_by_slug(slug: str) -> dict[str, Any]:
    from agents.rnd_dossier_agent import RndDossierAgent

    dossier = RndDossierAgent().get_dossier(slug)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")
    return dossier.model_dump()


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


@router.post("/rnd/dossiers/{dossier_id}/committee/start")
def rnd_committee_start(dossier_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    from agents.rnd_committee_agent import RndCommitteeAgent
    from services.rnd_schemas import RndCommitteeStartBody

    payload = RndCommitteeStartBody.model_validate(body or {})
    try:
        return RndCommitteeAgent().start_session(
            dossier_id,
            mode=payload.mode,
            active_section=payload.active_section,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_committee_start failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/rnd/dossiers/{dossier_id}/committee/sessions")
def rnd_committee_list_sessions(dossier_id: str) -> list[dict[str, Any]]:
    from agents.rnd_committee_agent import RndCommitteeAgent

    return RndCommitteeAgent().list_sessions(dossier_id)


@router.get("/rnd/dossiers/{dossier_id}/committee/{session_id}")
def rnd_committee_get_session(dossier_id: str, session_id: str) -> dict[str, Any]:
    from agents.rnd_committee_agent import RndCommitteeAgent

    try:
        return RndCommitteeAgent().get_session_with_messages(dossier_id, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/committee/{session_id}/message")
def rnd_committee_message(
    dossier_id: str,
    session_id: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    from agents.rnd_committee_agent import RndCommitteeAgent
    from services.rnd_schemas import RndCommitteeMessageBody

    payload = RndCommitteeMessageBody.model_validate(body)
    try:
        return RndCommitteeAgent().post_message(
            dossier_id,
            session_id,
            payload.message,
            target_speaker=payload.target_speaker,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_committee_message failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/committee/{session_id}/report")
def rnd_committee_generate_report(
    dossier_id: str,
    session_id: str,
) -> dict[str, Any]:
    """Génère le CR structuré sans clôturer la session comité."""
    from agents.rnd_committee_agent import RndCommitteeAgent

    try:
        return RndCommitteeAgent().generate_session_report(dossier_id, session_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_committee_generate_report failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/committee/{session_id}/close")
def rnd_committee_close(
    dossier_id: str,
    session_id: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from agents.rnd_committee_agent import RndCommitteeAgent
    from services.rnd_schemas import RndCommitteeCloseBody

    payload = RndCommitteeCloseBody.model_validate(body or {})
    try:
        return RndCommitteeAgent().close_session(
            dossier_id,
            session_id,
            apply_sections=payload.apply_sections,
            generate_ceo_package=payload.generate_ceo_package,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_committee_close failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc



RND_DOSSIERS_DATA_ROOT = data_dir("rnd_dossiers")


@router.get("/rnd/dossiers/{dossier_id}/assets")
def rnd_list_dossier_assets(dossier_id: str) -> list[dict[str, Any]]:
    from agents.rnd_visual_agent import RndVisualAgent

    try:
        assets = RndVisualAgent().list_assets(dossier_id)
        return [a.model_dump() for a in assets]
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/assets/generate")
def rnd_generate_dossier_assets(
    dossier_id: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from agents.rnd_visual_agent import RndVisualAgent
    from services.rnd_schemas import RndAssetsGenerateBody

    payload = RndAssetsGenerateBody.model_validate(body or {})
    try:
        result = RndVisualAgent().generate_assets(dossier_id, force=payload.force)
        result["assets"] = [
            {
                **a,
                "file_url": f"/rnd/dossiers/{dossier_id}/assets/file?asset_type={a['asset_type']}",
            }
            for a in result.get("assets", [])
        ]
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_generate_dossier_assets failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/rnd/dossiers/{dossier_id}/assets/file")
def rnd_dossier_asset_file(
    dossier_id: str,
    request: Request,
    asset_type: str | None = Query(default=None),
    asset_id: str | None = Query(default=None),
) -> FileResponse:
    from services.rnd_product import RndProductRepository
    from services.rnd_repository import get_rnd_repository

    if not asset_type and not asset_id:
        raise HTTPException(status_code=400, detail="asset_type ou asset_id requis")

    if not hub_api_key_valid(request.headers.get("X-Hub-Key")):
        page = RndProductRepository().get_by_dossier_id(dossier_id)
        if not page or not page.published:
            raise HTTPException(status_code=403, detail="Asset non public")

    dossier = get_rnd_repository().get_dossier(dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    assets = get_rnd_repository().list_assets(dossier.id)
    match = None
    if asset_id:
        match = next((a for a in assets if str(a.id) == str(asset_id)), None)
    elif asset_type:
        match = next((a for a in assets if a.asset_type == asset_type), None)
    if not match:
        raise HTTPException(status_code=404, detail="Asset introuvable")

    repo_root = get_hub_repo_path()
    data_root = RND_DOSSIERS_DATA_ROOT.resolve()

    path = Path(match.file_path)
    if not path.is_absolute():
        path = (repo_root / match.file_path.replace("\\", "/").lstrip("/")).resolve()
    else:
        path = path.resolve()

    if not str(path).startswith(str(data_root)):
        raise HTTPException(status_code=403, detail="Accès refusé")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Fichier asset introuvable")

    return FileResponse(path, media_type="image/png", filename=path.name)


@router.post("/rnd/dossiers/{dossier_id}/deck/generate")
def rnd_generate_deck(dossier_id: str, body: dict[str, Any] | None = None) -> dict[str, Any]:
    from services.rnd_deck import generate_dossier_deck

    export_pdf = True
    if body and "export_pdf" in body:
        export_pdf = bool(body["export_pdf"])
    try:
        result = generate_dossier_deck(dossier_id, export_pdf=export_pdf)
        dossier_id_resolved = result["dossier_id"]
        result["html_url"] = f"/rnd/dossiers/{dossier_id_resolved}/deck/file?type=html"
        if result.get("pdf_path"):
            result["pdf_url"] = f"/rnd/dossiers/{dossier_id_resolved}/deck/file?type=pdf"
        else:
            result["pdf_url"] = None
        return result
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_generate_deck failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/rnd/dossiers/{dossier_id}/deck/file")
def rnd_deck_file(
    dossier_id: str,
    type: str = Query(..., pattern="^(html|pdf)$"),
) -> FileResponse:
    from services.rnd_repository import get_rnd_repository

    dossier = get_rnd_repository().get_dossier(dossier_id)
    if not dossier:
        raise HTTPException(status_code=404, detail="Dossier introuvable")

    stored = dossier.deck_pdf_path if type == "pdf" else dossier.deck_html_path
    if not stored:
        raise HTTPException(status_code=404, detail="Deck non généré")

    repo_root = get_hub_repo_path()
    data_root = RND_DOSSIERS_DATA_ROOT.resolve()

    path = Path(stored)
    if not path.is_absolute():
        path = (repo_root / stored.replace("\\", "/").lstrip("/")).resolve()
    else:
        path = path.resolve()

    if not str(path).startswith(str(data_root)):
        raise HTTPException(status_code=403, detail="Accès refusé")
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Fichier deck introuvable")

    media = "application/pdf" if type == "pdf" else "text/html"
    return FileResponse(path, media_type=media, filename=path.name)




@router.get("/rnd/dossiers/{dossier_id}/social/calendar")
def rnd_social_list_calendar(dossier_id: str) -> list[dict[str, Any]]:
    from agents.rnd_social_agent import RndSocialAgent

    try:
        return RndSocialAgent().list_calendar(dossier_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/rnd/dossiers/{dossier_id}/social/status")
def rnd_social_status(dossier_id: str) -> dict[str, Any]:
    from agents.rnd_social_agent import RndSocialAgent

    try:
        return RndSocialAgent().social_status(dossier_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/social/calendar/generate")
def rnd_social_generate_calendar(
    dossier_id: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from agents.rnd_social_agent import RndSocialAgent
    from services.rnd_schemas import RndSocialCalendarGenerateBody
    from services.rnd_social import SocialPipelineLockedError

    payload = RndSocialCalendarGenerateBody.model_validate(body or {})
    try:
        return RndSocialAgent().generate_calendar(
            dossier_id,
            force=payload.force,
            launch_date=payload.launch_date,
        )
    except SocialPipelineLockedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_social_generate_calendar failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch("/rnd/dossiers/{dossier_id}/social/calendar/{item_id}")
def rnd_social_patch_calendar(
    dossier_id: str,
    item_id: str,
    body: dict[str, Any],
) -> dict[str, Any]:
    from agents.rnd_social_agent import RndSocialAgent
    from services.rnd_schemas import RndSocialPatchCalendarBody

    payload = RndSocialPatchCalendarBody.model_validate(body)
    try:
        return RndSocialAgent().patch_calendar_item(
            dossier_id,
            item_id,
            payload.model_dump(exclude_none=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/social/calendar/{item_id}/generate-post")
def rnd_social_generate_post(
    dossier_id: str,
    item_id: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from agents.rnd_social_agent import RndSocialAgent
    from services.rnd_schemas import RndSocialGeneratePostBody
    from services.rnd_social import SocialPipelineLockedError

    payload = RndSocialGeneratePostBody.model_validate(body or {})
    try:
        return RndSocialAgent().generate_post_for_item(
            dossier_id,
            item_id,
            platforms=payload.platforms,
        )
    except SocialPipelineLockedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_social_generate_post failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/social/generate-all")
def rnd_social_generate_all(dossier_id: str) -> dict[str, Any]:
    from agents.rnd_social_agent import RndSocialAgent
    from services.rnd_social import SocialPipelineLockedError

    try:
        return RndSocialAgent().generate_all_posts(dossier_id)
    except SocialPipelineLockedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_social_generate_all failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/rnd/dossiers/{dossier_id}/social/posts")
def rnd_social_list_posts(dossier_id: str) -> list[dict[str, Any]]:
    from agents.rnd_social_agent import RndSocialAgent

    try:
        return RndSocialAgent().list_posts(dossier_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc




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


@router.get("/rnd/product/{slug}")
def rnd_public_product_page(slug: str) -> dict[str, Any]:
    """Fiche produit publique (published=true uniquement)."""
    from agents.rnd_product_agent import RndProductAgent

    try:
        return RndProductAgent().get_public_page(slug)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/rnd/dossiers/{dossier_id}/product")
def rnd_get_product_page(dossier_id: str) -> dict[str, Any]:
    from agents.rnd_product_agent import RndProductAgent

    try:
        return RndProductAgent().get_product_page(dossier_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/rnd/dossiers/{dossier_id}/product/status")
def rnd_product_status(dossier_id: str) -> dict[str, Any]:
    from agents.rnd_product_agent import RndProductAgent

    try:
        return RndProductAgent().product_status(dossier_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/product/generate")
def rnd_generate_product_page(
    dossier_id: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from agents.rnd_product_agent import RndProductAgent
    from services.rnd_product import ProductPipelineLockedError
    from services.rnd_schemas import RndProductGenerateBody

    payload = RndProductGenerateBody.model_validate(body or {})
    try:
        return RndProductAgent().generate_product_page(
            dossier_id,
            force=payload.force,
            waitlist_enabled=payload.waitlist_enabled,
        )
    except ProductPipelineLockedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_generate_product_page failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.patch("/rnd/dossiers/{dossier_id}/product")
def rnd_patch_product_page(dossier_id: str, body: dict[str, Any]) -> dict[str, Any]:
    from agents.rnd_product_agent import RndProductAgent
    from services.rnd_schemas import RndProductPatchBody

    payload = RndProductPatchBody.model_validate(body)
    values = payload.model_dump(exclude_none=True)
    try:
        return RndProductAgent().update_product_page(dossier_id, values=values)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/product/publish")
def rnd_publish_product_page(dossier_id: str) -> dict[str, Any]:
    from agents.rnd_product_agent import RndProductAgent
    from services.rnd_product import ProductPipelineLockedError

    try:
        return RndProductAgent().publish_product_page(dossier_id)
    except ProductPipelineLockedError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_publish_product_page failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/dossiers/{dossier_id}/product/unpublish")
def rnd_unpublish_product_page(dossier_id: str) -> dict[str, Any]:
    from agents.rnd_product_agent import RndProductAgent

    try:
        return RndProductAgent().unpublish_product_page(dossier_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/finances/summary/{month}")
def get_finance_summary(month: str) -> dict[str, Any]:
    try:
        return get_or_generate_summary(month)
    except Exception as exc:
        logger.exception("Finance summary failed for %s", month)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/finances/summary/generate")
def regenerate_finance_summary(body: FinanceSummaryGenerate) -> dict[str, Any]:
    try:
        return generate_monthly_summary(body.month, force=True)
    except Exception as exc:
        logger.exception("Finance summary regeneration failed for %s", body.month)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/finances/dashboard")
def finance_dashboard(
    month: str | None = Query(default=None, pattern=r"^\d{4}-\d{2}$"),
) -> dict[str, Any]:
    db = get_supabase()
    data = build_dashboard(db, month=month)
    data["recurring_expenses"] = attach_project_names(
        db, data["recurring_expenses"]
    )
    return data


