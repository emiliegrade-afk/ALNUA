"""R&D Center — ideas JSON store + vision + CRUD helpers."""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("rnd_center")

RND_IDEAS_FILE = Path(os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB")) / "data" / "rnd_ideas.json"



# ---------------------------------------------------------------------------
# Vision & fil conducteur
# ---------------------------------------------------------------------------

def get_vision() -> str:
    """Récupère le fil conducteur R&D depuis Mem0 + leçons apprises."""
    base = (
        "ALNUA — société d'Emilie (CEO solopreneuse). "
        "Portfolio : NUAWAY (app mobilité / voyage — UN produit, pas toute la société), "
        "Naïa (bien-être), Wyrdheim (gaming), Eve (robotique), Hub IA (agents). "
        "ALNUA explore TOUS les marchés : gaming, santé, robotique, SaaS B2B, hardware, "
        "créateurs, productivité — ne pas recentrer la société sur un seul produit ou audience. "
        "Règle R&D : diversifier ; max ~1 idée vanlife/nomad (segment NUAWAY) par cycle de 6 idées."
    )
    try:
        from skills.skill_mem0 import recall
        from skills.skill_agent_learning import get_learning_context

        vision = recall("fil conducteur vision R&D ALNUA", agent_id="rnd_agent")
        if vision and len(vision) > 20:
            base = vision
        lessons = get_learning_context("rnd_agent", "cycle R&D vision fil conducteur")
        if lessons:
            base += lessons
    except Exception:
        pass
    return base


def set_vision(new_vision: str) -> None:
    """Met à jour le fil conducteur. Appelé par le COO sur instruction d'Emilie."""
    try:
        from skills.skill_mem0 import remember
        remember(
            f"[Fil conducteur R&D mis à jour {datetime.now().strftime('%Y-%m-%d')}] {new_vision}",
            agent_id="rnd_agent",
        )
        logger.info("rnd_center: vision mise à jour")
    except Exception as exc:
        logger.warning("rnd_center: set_vision failed: %s", exc)


# ---------------------------------------------------------------------------
# Persistance des idées
# ---------------------------------------------------------------------------

def _load_ideas() -> list[dict]:
    try:
        RND_IDEAS_FILE.parent.mkdir(parents=True, exist_ok=True)
        if RND_IDEAS_FILE.exists():
            return json.loads(RND_IDEAS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return []


def _save_ideas(ideas: list[dict]) -> None:
    try:
        RND_IDEAS_FILE.parent.mkdir(parents=True, exist_ok=True)
        # Dedupe by id — parallel cycles may race on the same file.
        by_id: dict[str, dict] = {}
        for idea in ideas:
            idea_id = idea.get("id")
            if idea_id:
                by_id[idea_id] = idea
        merged = list(by_id.values())
        RND_IDEAS_FILE.write_text(
            json.dumps(merged, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        # Dual-write to Supabase rnd_ideas (phase 1+)
        try:
            from services.rnd_repository import get_rnd_repository
            get_rnd_repository().save_ideas_json(merged)
        except Exception as sync_exc:
            logger.warning("rnd_center: supabase dual-write failed: %s", sync_exc)
    except Exception as exc:
        logger.warning("rnd_center: save_ideas failed: %s", exc)


def inject_idea(idea: str, source: str = "Emilie") -> dict:
    """
    Injecte une idée d'Emilie dans le pipeline R&D.
    Elle sera évaluée et scorée au prochain cycle.
    """
    ideas = _load_ideas()
    new_idea = {
        "id": f"idea_{int(datetime.now().timestamp())}",
        "title": idea[:100],
        "description": idea,
        "source": source,
        "status": "pending_evaluation",
        "score": None,
        "created_at": datetime.now().isoformat(),
        "domain": "à déterminer",
    }
    ideas.append(new_idea)
    _save_ideas(ideas)
    logger.info("rnd_center: idée injectée par %s : %s", source, idea[:60])
    return new_idea


def get_top_ideas(
    limit: int = 5,
    verdict: str | None = None,
    inbox_only: bool = False,
) -> list[dict]:
    """Retourne les meilleures idées du journal R&D. Utile pour le COO."""
    try:
        from services.rnd_repository import get_rnd_repository
        api_ideas = get_rnd_repository().get_top_ideas(
            limit=limit, verdict=verdict, inbox_only=inbox_only
        )
        if api_ideas:
            return [
                {
                    "id": i.id,
                    "db_id": i.db_id,
                    "title": i.title,
                    "description": i.description,
                    "source": i.source,
                    "status": i.status,
                    "score": i.score,
                    "market_score": i.market_score,
                    "feasibility_score": i.feasibility_score,
                    "vision_score": i.vision_score,
                    "verdict": i.verdict,
                    "reasoning": i.reasoning,
                    "verdict_reason": i.verdict_reason,
                    "next_step": i.next_step,
                    "why_now": i.why_now,
                    "effort": i.effort,
                    "domain": i.domain,
                    "spec_file": i.spec_file,
                    "lifecycle_status": i.lifecycle_status,
                    "dossier_id": i.dossier_id,
                    "incubator_stage": i.incubator_stage,
                    "created_at": i.created_at,
                    "evaluated_at": i.evaluated_at,
                }
                for i in api_ideas
            ]
    except Exception as exc:
        logger.warning("rnd_center: get_top_ideas via repository failed: %s", exc)

    ideas = _load_ideas()
    if inbox_only:
        ideas = [
            i for i in ideas
            if not i.get("dossier_id") and i.get("lifecycle_status") != "archived"
        ]
    if verdict:
        ideas = [i for i in ideas if i.get("verdict") == verdict.upper()]
    return sorted(ideas, key=lambda x: x.get("score") or 0, reverse=True)[:limit]


def archive_idea(idea_id: str) -> bool:
    """Archive une proposition R&D (soft delete)."""
    from services.rnd_repository import get_rnd_repository

    return get_rnd_repository().archive_idea(idea_id)


def get_idea_by_id(idea_id: str) -> dict | None:
    """Retourne une idée par legacy_id ou UUID."""
    try:
        from services.rnd_repository import get_rnd_repository
        idea = get_rnd_repository().get_idea_by_id(idea_id)
        if idea:
            return idea.model_dump()
    except Exception as exc:
        logger.warning("rnd_center: get_idea_by_id failed: %s", exc)
    for item in _load_ideas():
        if item.get("id") == idea_id:
            return item
    return None
