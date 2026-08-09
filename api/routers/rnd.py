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
def rnd_get_ideas(
    limit: int = Query(default=20, le=100),
    verdict: str | None = None,
    inbox_only: bool = Query(default=True, description="Exclure idées promues/archivées"),
) -> list[dict]:
    """Retourne les idées générées par le Centre R&D, triées par score."""
    try:
        from agents.rnd_center import get_top_ideas
        return get_top_ideas(limit=limit, verdict=verdict, inbox_only=inbox_only)
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
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/submit")
def rnd_submit_user_dossier(body: dict[str, Any]) -> dict[str, Any]:
    """Soumet un dossier R&D structuré (idée + sections) — création directe sans cycle auto."""
    from agents.rnd_dossier_agent import RndDossierAgent

    try:
        return RndDossierAgent().submit_user_dossier(body, actor="emilie")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_submit_user_dossier failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/investigate")
def rnd_start_investigation(body: dict[str, Any]) -> dict[str, Any]:
    """Launch Arbor-lite hypothesis tree investigation (async)."""
    topic = str(body.get("topic") or body.get("query") or "").strip()
    if len(topic) < 3:
        raise HTTPException(status_code=400, detail="topic requis (min 3 caractères)")
    try:
        from services.rnd_hypothesis_tree import start_investigation

        return start_investigation(
            topic,
            requested_by=str(body.get("requested_by") or "ceo"),
            chat_id=body.get("chat_id"),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_start_investigation failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/rnd/trees")
def rnd_list_trees(limit: int = Query(default=20, le=50)) -> dict[str, Any]:
    from services.rnd_hypothesis_tree import list_trees

    return {"trees": list_trees(limit=limit)}


@router.get("/rnd/trees/{slug}")
def rnd_get_tree(slug: str) -> dict[str, Any]:
    from services.rnd_hypothesis_tree import get_tree

    tree = get_tree(slug)
    if not tree:
        raise HTTPException(status_code=404, detail="Arbre introuvable")
    return tree


@router.get("/rnd/watch-topics")
def rnd_watch_topics() -> dict[str, Any]:
    from services.rnd_hypothesis_tree import get_watch_topics

    return {"topics": get_watch_topics()}


@router.get("/rnd/trees/{slug}/graph")
def rnd_tree_graph(slug: str) -> dict[str, Any]:
    from services.rnd_hypothesis_tree import build_tree_graph

    graph = build_tree_graph(slug)
    if not graph:
        raise HTTPException(status_code=404, detail="Arbre introuvable")
    return graph


@router.post("/rnd/trees/{slug}/nodes/{node_id}/expand")
def rnd_expand_node(
    slug: str,
    node_id: str,
    body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    req = body or {}
    try:
        from services.rnd_hypothesis_tree import expand_node

        manual = None
        if req.get("title"):
            manual = {
                "title": str(req["title"])[:200],
                "hypothesis": str(req.get("hypothesis") or req["title"])[:2000],
            }
        return expand_node(
            slug,
            node_id,
            max_children=int(req.get("max_children") or 3),
            run_after=bool(req.get("run_after")),
            manual=manual,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_expand_node failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/trees/{slug}/nodes/{node_id}/run")
def rnd_run_node(slug: str, node_id: str) -> dict[str, Any]:
    try:
        from services.rnd_hypothesis_tree import run_node

        return run_node(slug, node_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.patch("/rnd/trees/{slug}/nodes/{node_id}")
def rnd_patch_node(slug: str, node_id: str, body: dict[str, Any]) -> dict[str, Any]:
    status = str(body.get("status") or "").strip()
    if not status:
        raise HTTPException(status_code=400, detail="status requis")
    try:
        from services.rnd_hypothesis_tree import set_node_status

        return set_node_status(slug, node_id, status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.patch("/rnd/trees/{slug}/nodes/{node_id}/reparent")
def rnd_reparent_node(slug: str, node_id: str, body: dict[str, Any]) -> dict[str, Any]:
    """Glisser un nœud sur un autre dans le canvas Arbres (Phase 26, ROADMAP.md) = "relier"."""
    new_parent_id = str(body.get("new_parent_id") or "").strip()
    if not new_parent_id:
        raise HTTPException(status_code=400, detail="new_parent_id requis")
    try:
        from services.rnd_hypothesis_tree import reparent_node

        return reparent_node(slug, node_id, new_parent_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_reparent_node failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/trees/{slug}/nodes/{node_id}/promote")
def rnd_promote_tree_node(
    slug: str,
    node_id: str,
    enrich: bool = Query(default=True, alias="enrich"),
) -> dict[str, Any]:
    try:
        from services.rnd_hypothesis_tree import promote_node_to_dossier

        return promote_node_to_dossier(slug, node_id, enrich=enrich)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_promote_tree_node failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/rnd/benchmark/llm-latency")
def rnd_run_llm_benchmark(body: dict[str, Any] | None = None) -> dict[str, Any]:
    """Benchmark OpenRouter vs DiffusionGemma reference on short Hub tasks."""
    req = body or {}
    try:
        from services.rnd_llm_benchmark import run_llm_latency_benchmark

        return run_llm_latency_benchmark(
            agent_id=str(req.get("agent_id") or "secretary"),
            prompts=req.get("prompts"),
        )
    except Exception as exc:
        logger.exception("rnd_run_llm_benchmark failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("/rnd/benchmark/llm-latency/latest")
def rnd_latest_llm_benchmark() -> dict[str, Any]:
    from services.rnd_llm_benchmark import get_latest_benchmark

    latest = get_latest_benchmark()
    if not latest:
        return {"benchmark": None, "message": "Aucun benchmark — lance POST /rnd/benchmark/llm-latency"}
    return {"benchmark": latest}


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


@router.delete("/rnd/ideas/{idea_id}")
def rnd_archive_idea(idea_id: str) -> dict[str, str]:
    """Archive une proposition R&D (retire de la liste inbox)."""
    from agents.rnd_center import archive_idea

    try:
        if not archive_idea(idea_id):
            raise HTTPException(status_code=404, detail=f"Idée introuvable : {idea_id}")
        return {"ok": "Idée archivée"}
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_archive_idea failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


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


@router.patch("/rnd/ideas/{idea_id}/incubator-stage")
def rnd_set_incubator_stage(idea_id: str, body: dict[str, Any]) -> dict[str, Any]:
    """Incubateur (Phase 24) — glisser une carte vers une colonne
    intermédiaire (Idée/Prototype/Validation/MVP/Projet). Simple étiquette,
    aucune conséquence réelle — voir promote-to-department pour la colonne
    Département, qui elle déclenche un vrai dispatch."""
    from datetime import datetime, timezone

    from services.rnd_repository import get_rnd_repository
    from services.rnd_schemas import RndIncubatorStageBody

    payload = RndIncubatorStageBody.model_validate(body)
    if payload.stage == "departement":
        raise HTTPException(
            status_code=400,
            detail="Utilise POST /rnd/ideas/{idea_id}/incubator/promote-to-department pour la colonne Département.",
        )

    repo = get_rnd_repository()
    idea_row = repo.get_idea_db_row(idea_id)
    if not idea_row:
        raise HTTPException(status_code=404, detail=f"Idée introuvable : {idea_id}")

    repo.db.update(
        "rnd_ideas",
        idea_row["id"],
        {
            "incubator_stage": payload.stage,
            "incubator_stage_updated_at": datetime.now(timezone.utc).isoformat(),
        },
    )
    return {"idea_id": idea_id, "incubator_stage": payload.stage}


@router.post("/rnd/ideas/{idea_id}/incubator/promote-to-department")
def rnd_promote_idea_to_department(idea_id: str) -> dict[str, Any]:
    """Incubateur (Phase 24) — glisser une carte vers la colonne Département.
    Geste d'approbation CEO explicite : crée le dossier si absent, génère le
    package CEO si éligible, approuve, dispatch. Refuse honnêtement
    (403) si le dossier n'a pas encore de rapport comité plutôt que de
    fabriquer une approbation."""
    from agents.rnd_ceo_agent import CeoDecisionError, CeoPackageNotReadyError, DispatchNotAllowedError, RndCeoAgent

    try:
        result = RndCeoAgent().promote_idea_to_department(idea_id, actor="emilie")
    except CeoPackageNotReadyError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (CeoDecisionError, DispatchNotAllowedError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("rnd_promote_idea_to_department failed for %s", idea_id)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    from datetime import datetime, timezone

    from services.rnd_repository import get_rnd_repository

    repo = get_rnd_repository()
    idea_row = repo.get_idea_db_row(idea_id)
    if idea_row:
        repo.db.update(
            "rnd_ideas",
            idea_row["id"],
            {
                "incubator_stage": "departement",
                "incubator_stage_updated_at": datetime.now(timezone.utc).isoformat(),
            },
        )
    return result


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
            force_new=payload.force_new,
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


# Finance summary/dashboard: canonical handlers in api/routers/finances.py (Phase 4).
# Paths unchanged — implementation moved out of this god router.
