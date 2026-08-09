"""R&D Center — market / competitor / user feedback observation."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from agents.rnd_center_llm import _llm
from config.agent_operating_spec import get_system_prompt

logger = logging.getLogger("rnd_center")

# ---------------------------------------------------------------------------
# Concurrents par produit ALNUA
# ---------------------------------------------------------------------------

COMPETITOR_MAP = {
    "nuaway": {
        "apps": ["Park4Night", "iOverlander", "Campendium", "Freecampsites", "The Dyrt", "Vanlife App"],
        "queries": [
            "Park4Night app review complaints problems 2025 2026",
            "iOverlander app negative review what users hate",
            "vanlife app review Reddit frustration missing features",
            "camping app review complaints offline slow bugs",
            "nomad van life app store review 1 star problems",
        ],
    },
    "naia": {
        "apps": ["No Man's Sky", "Minecraft", "Dwarf Fortress", "Valheim", "Stardew Valley", "AI Dungeon"],
        "queries": [
            "No Man's Sky negative review what players hate 2025",
            "open world AI game review complaints Reddit",
            "procedural generation game boring repetitive player feedback",
            "indie open world game Steam review 1 star problems",
            "AI NPC game review what players dislike 2025",
        ],
    },
    "hub": {
        "apps": ["Monday.com", "Notion AI", "ClickUp", "Zapier", "Make", "AutoGPT"],
        "queries": [
            "AI agent tool review complaints what users hate 2025 2026",
            "Notion AI review negative feedback problems",
            "automation tool solopreneur frustrations Reddit",
            "AI productivity app 1 star review common complaints",
            "no-code AI tool problems limitations review",
        ],
    },
}


def _ddgs_search(query: str, max_results: int = 3, timeout: int = 15) -> list[dict]:
    """Wrapper DDGS avec timeout via thread — évite les blocages indéfinis."""
    import concurrent.futures
    def _do_search():
        from ddgs import DDGS
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(_do_search)
            return future.result(timeout=timeout)
    except Exception:
        return []


def _scrape_competitor_reviews() -> dict[str, str]:
    """
    Recherche les avis négatifs sur les apps concurrentes pour chaque produit ALNUA.
    Retourne {produit: texte_des_avis_compilés}
    Timeout strict : 15s par requête, 1 requête par produit max.
    """
    try:
        from ddgs import DDGS  # noqa: F401
    except ImportError:
        return {}

    results_by_product = {}
    for product, config in COMPETITOR_MAP.items():
        snippets = []
        # 1 seule query par produit pour limiter le temps
        query = config["queries"][0]
        hits = _ddgs_search(query, max_results=5, timeout=15)
        for h in hits:
            text = h.get("body", "")
            if any(w in text.lower() for w in ["bad", "issue", "bug", "problem", "missing", "complaint", "frustrat", "crash"]):
                snippets.append(f"[{h.get('title', '')}] {text[:300]}")
        if snippets:
            results_by_product[product] = "\n\n".join(snippets[:6])

    return results_by_product


def _analyze_competitor_pain_points(raw_reviews: dict[str, str], vision: str) -> str:
    """
    LLM analyse les avis négatifs concurrents et extrait :
    - Les erreurs à ne PAS répéter
    - Les fonctionnalités manquantes que les users réclament
    - Les opportunités de différenciation
    """
    if not raw_reviews:
        return ""

    reviews_block = "\n\n".join(
        f"=== {product.upper()} (concurrents) ===\n{text[:1500]}"
        for product, text in raw_reviews.items()
    )

    system = get_system_prompt("rnd_competitor_pain")

    user = f"""VISION ALNUA : {vision[:400]}

AVIS NÉGATIFS CONCURRENTS :
{reviews_block}

Analyse et extrais les leçons à retenir pour éviter ces erreurs dans NUAWAY, Naïa et Hub."""

    try:
        return _llm(system, user, max_tokens=2000)
    except Exception as exc:
        logger.warning("rnd_center: analyze_competitor_pain_points failed: %s", exc)
        return ""


def _store_anti_patterns(analysis: str, cycle_date: str) -> None:
    """
    Sauvegarde l'analyse dans Mem0 (par agent concerné) + fichier markdown.
    Les agents apprendront à éviter ces erreurs dans leurs tâches quotidiennes.
    """
    if not analysis:
        return

    try:
        from skills.skill_mem0 import remember

        # COO et R&D reçoivent l'analyse complète
        remember(
            f"[Anti-patterns concurrents {cycle_date}] {analysis[:800]}",
            agent_id="rnd_agent",
        )
        remember(
            f"[Leçons concurrents {cycle_date}] Erreurs à éviter dans nos produits : {analysis[:400]}",
            agent_id="coo",
        )

        # Agents dev reçoivent les anti-patterns techniques
        if "NUAWAY" in analysis or "nuaway" in analysis.lower():
            remember(
                f"[Anti-patterns NUAWAY {cycle_date}] Ce que les users détestent chez Park4Night & co : {analysis[:500]}",
                agent_id="dev_app",
            )
        if "NAIA" in analysis or "naia" in analysis.lower():
            remember(
                f"[Anti-patterns Naïa {cycle_date}] Ce que les joueurs détestent chez les concurrents : {analysis[:500]}",
                agent_id="dev_gaming",
            )
            remember(
                f"[Leçons game design {cycle_date}] Erreurs des concurrents à éviter : {analysis[:500]}",
                agent_id="game_director",
            )

        # Sauvegarde le fichier markdown
        reports_dir = Path(os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB")) / "data" / "rnd_competitive"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_file = reports_dir / f"{cycle_date}_competitor_analysis.md"
        report_file.write_text(
            f"# Analyse concurrentielle ALNUA — {cycle_date}\n\n{analysis}",
            encoding="utf-8",
        )
        logger.info("rnd_center: anti-patterns sauvegardés → %s", report_file.name)

    except Exception as exc:
        logger.warning("rnd_center: store_anti_patterns failed: %s", exc)


# ---------------------------------------------------------------------------
# ÉTAPE 1 — Observer le marché
# ---------------------------------------------------------------------------

def _observe_market(vision: str) -> str:
    """
    Recherche web sur les tendances marché actuelles.
    2 requêtes max, timeout strict 15s chacune.
    """
    try:
        from ddgs import DDGS  # noqa: F401
    except ImportError:
        return "ddgs non disponible."

    queries = [
        "best startup app ideas 2026 solopreneur trending",
        "consumer robotics AI hardware startup trends 2026",
        "indie game SaaS health app market opportunity 2026",
    ]
    observations = []
    for q in queries:
        results = _ddgs_search(q, max_results=3, timeout=15)
        for r in results:
            observations.append(f"[{q}] {r.get('title', '')}: {r.get('body', '')[:200]}")
    return "\n".join(observations[:12]) if observations else "Aucune observation marché disponible."


def _observe_user_feedback(vision: str) -> str:
    """Lit les feedbacks users depuis Supabase + journal erreurs."""
    observations = []
    try:
        from database.supabase_client import get_supabase
        db = get_supabase()
        feedback = (
            db.raw.table("feedback")
            .select("content, project_id, rating, created_at")
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        if feedback.data:
            for f in feedback.data:
                observations.append(
                    f"[Feedback {f.get('project_id', '?')} — {f.get('rating', '?')}/5] {f.get('content', '')[:150]}"
                )
    except Exception:
        pass

    try:
        from skills.skill_error_journal import get_open_errors_summary
        errors = get_open_errors_summary()
        if not errors.startswith("[OK]"):
            observations.append(f"[Bugs récurrents] {errors[:300]}")
    except Exception:
        pass

    return "\n".join(observations) if observations else "Aucun feedback récent disponible."

