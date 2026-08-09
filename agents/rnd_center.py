"""R&D Center — façade BUG-004 (cycle + re-exports)."""
from __future__ import annotations

import logging
import threading
from datetime import datetime
from typing import Any

from agents.rnd_center_library import (  # noqa: F401
    _expand_library_concept,
    develop_idea_from_library,
    develop_library_entries_as_rnd,
    develop_pending_library_ideas,
    develop_rnd_ideas_from_ceo_report,
    submit_user_proposal,
)
from agents.rnd_center_llm import OPENROUTER_BASE, _llm, _rnd_model  # noqa: F401
from agents.rnd_center_observe import (  # noqa: F401
    COMPETITOR_MAP,
    _analyze_competitor_pain_points,
    _observe_market,
    _observe_user_feedback,
    _scrape_competitor_reviews,
    _store_anti_patterns,
)
from agents.rnd_center_pipeline import (  # noqa: F401
    _build_report,
    _evaluate_idea,
    _generate_ideas,
    _prototype_idea,
    _send_telegram,
    build_rnd_diversity_block,
    count_recent_vanlife_ideas,
)
from agents.rnd_center_store import (  # noqa: F401
    RND_IDEAS_FILE,
    _load_ideas,
    _save_ideas,
    archive_idea,
    get_idea_by_id,
    get_top_ideas,
    get_vision,
    inject_idea,
    set_vision,
)

logger = logging.getLogger("rnd_center")

def run_rnd_cycle(blocking: bool = True) -> dict[str, Any]:
    """
    Lance un cycle R&D complet.
    Appelé : hebdomadaire (scheduler) ou sur demande du COO.
    """
    def _run():
        cycle_date = datetime.now().strftime("%Y-%m-%d")
        logger.info("rnd_center: démarrage cycle R&D %s", cycle_date)

        # Charge la vision et les idées existantes
        vision = get_vision()
        existing_ideas = _load_ideas()
        existing_titles = [i["title"] for i in existing_ideas]

        # 1. Observer — marché + avis négatifs concurrents + feedback users
        logger.info("rnd_center: observation marché + analyse concurrents...")
        market_obs = _observe_market(vision)
        user_feedback = _observe_user_feedback(vision)

        # Analyse des avis négatifs concurrents — ce qu'il ne faut PAS faire
        logger.info("rnd_center: scraping avis concurrents (Park4Night, No Man's Sky, etc.)...")
        raw_reviews = _scrape_competitor_reviews()
        competitor_analysis = _analyze_competitor_pain_points(raw_reviews, vision)
        _store_anti_patterns(competitor_analysis, cycle_date)

        # Injecte l'analyse concurrente dans le contexte de génération d'idées
        if competitor_analysis:
            market_obs = f"{market_obs}\n\n=== CE QUE LES USERS DÉTESTENT CHEZ LES CONCURRENTS ===\n{competitor_analysis[:1000]}"

        # 2. Générer
        logger.info("rnd_center: génération d'idées...")
        new_ideas = _generate_ideas(market_obs, user_feedback, vision, existing_titles)

        # 3. Évaluer les idées générées + les idées injectées par Emilie (pending)
        pending = [i for i in existing_ideas if i.get("status") == "pending_evaluation"]
        to_evaluate = new_ideas + pending
        logger.info("rnd_center: évaluation de %d idées...", len(to_evaluate))

        evaluated = []
        for idea in to_evaluate:
            evaluated.append(_evaluate_idea(idea, vision))

        # 4. Prototyper les idées GO avec effort S ou M
        prototyped_files = []
        go_ideas = [i for i in evaluated if i.get("verdict") == "GO" and i.get("effort") in ("S", "M")]
        for idea in go_ideas[:2]:  # Max 2 prototypes par cycle
            spec_path = _prototype_idea(idea)
            if spec_path:
                prototyped_files.append(spec_path)
                idea["status"] = "prototyped"
            else:
                idea["status"] = "go_pending_prototype"

        # Autres statuts
        for idea in evaluated:
            if idea.get("status") == "pending_evaluation":
                idea["status"] = f"evaluated_{idea.get('verdict', 'unknown').lower()}"

        # 5. Sauvegarde toutes les idées (sans doublons)
        merged: dict[str, dict] = {
            i["id"]: i
            for i in existing_ideas
            if i.get("id") and i.get("status") != "pending_evaluation"
        }
        for idea in evaluated:
            if idea.get("id"):
                merged[idea["id"]] = idea
        _save_ideas(list(merged.values()))

        # Enregistre dans Mem0 les top idées
        try:
            from skills.skill_mem0 import remember
            top = [i for i in evaluated if i.get("verdict") == "GO"][:3]
            if top:
                summary = f"Cycle R&D {cycle_date} — Top idées GO : " + " | ".join(
                    f"{i['title']} ({i.get('domain', '?')}, score {i.get('score', 0)}/30)" for i in top
                )
                remember(summary, agent_id="rnd_agent")
                remember(summary, agent_id="coo")
        except Exception:
            pass

        # 6. Rapport
        report = _build_report(evaluated, prototyped_files, cycle_date)
        logger.info("rnd_center: cycle terminé — %d idées, %d prototypes", len(evaluated), len(prototyped_files))
        logger.info("rnd_center report:\n%s", report)

        # Telegram (async depuis un thread — on essaie)
        try:
            import asyncio
            loop = asyncio.new_event_loop()
            loop.run_until_complete(_send_telegram(report))
            loop.close()
        except Exception:
            pass

        try:
            from skills.skill_agent_learning import record_task_learning

            record_task_learning(
                agent_id="rnd_agent",
                task=f"cycle R&D {cycle_date}",
                outcome=report[:600],
                success=True,
            )
        except Exception:
            pass

        return {
            "ideas_generated": len(new_ideas),
            "ideas_evaluated": len(evaluated),
            "go_count": len([i for i in evaluated if i.get("verdict") == "GO"]),
            "prototyped": len(prototyped_files),
            "report": report,
        }

    if blocking:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(_run)
            try:
                return future.result(timeout=600)  # 10 min max
            except concurrent.futures.TimeoutError:
                logger.error("rnd_center: cycle timeout après 10 min")
                return {"status": "timeout", "ideas_generated": 0}
    else:
        threading.Thread(target=_run, daemon=True).start()
        return {"status": "cycle R&D lancé en arrière-plan"}


