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

