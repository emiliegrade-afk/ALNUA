"""
rnd_center.py — Centre R&D Autonome ALNUA.

Inspiré de AI Scientist (Sakana AI) — les agents font leur propre R&D.

Cycle hebdomadaire autonome :
    1. Observer — marché, concurrents, tendances, feedback users
    2. Générer — idées sans limites de domaine (app, jeu, robotique, IA, hardware...)
    3. Évaluer — score impact / faisabilité / potentiel marché
    4. Prototyper — les meilleures petites idées → spec ou ticket dev
    5. Rapporter — Telegram + Mem0 → COO informé

Aucune bride sur les idées. Le seul filtre : "y a-t-il un marché ?"
Les agents explorent librement dans le cadre de la vision d'Emilie.

Usage :
    from agents.rnd_center import run_rnd_cycle, inject_idea, set_vision
    run_rnd_cycle()                                # cycle complet
    inject_idea("App de gestion de van en mode offline first")
    set_vision("Focus Q3 : monétisation + robotique accessible")
"""
from __future__ import annotations

import json
import logging
import os
import threading
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from config.settings import get_settings

logger = logging.getLogger(__name__)

OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"


def _rnd_model() -> str:
    """Prefer a JSON-reliable model; minimax-m1 often returns reasoning-only text."""
    from agents.base import resolve_openrouter_model, to_api_model_slug

    env_override = os.getenv("RND_MODEL", "").strip()
    if env_override:
        return to_api_model_slug(env_override)
    return resolve_openrouter_model("rnd_agent")


def _extract_message_text(message: dict[str, Any]) -> str:
    """OpenRouter reasoning models may leave content null and use reasoning fields."""
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content.strip()

    reasoning = message.get("reasoning")
    if isinstance(reasoning, str) and reasoning.strip():
        return reasoning.strip()

    parts: list[str] = []
    for detail in message.get("reasoning_details") or []:
        if isinstance(detail, dict) and detail.get("text"):
            parts.append(str(detail["text"]))
    return "\n".join(parts).strip()

# Fichier local pour persister les idées entre sessions
RND_IDEAS_FILE = Path(os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB")) / "data" / "rnd_ideas.json"


# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

def _openrouter_key() -> str:
    return get_settings().openrouter_api_key.strip()


def _llm(system: str, user: str, model: str | None = None, max_tokens: int = 4000) -> str:
    api_key = _openrouter_key()
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY manquante dans .env")

    model_slug = (model or _rnd_model()).replace("openrouter/", "")

    payload = json.dumps({
        "model": model_slug,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.8,  # Plus élevé pour la créativité R&D
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        OPENROUTER_BASE,
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.loads(r.read())
    message = data["choices"][0]["message"]
    text = _extract_message_text(message)
    if not text:
        raise RuntimeError(f"Réponse LLM vide (model={model_slug})")
    return text


# ---------------------------------------------------------------------------
# Vision & fil conducteur
# ---------------------------------------------------------------------------

def get_vision() -> str:
    """Récupère le fil conducteur R&D depuis Mem0 + leçons apprises."""
    base = (
        "ALNUA est une société virtuelle dirigée par Emilie, solopreneuse nomade. "
        "Stack actuelle : NUAWAY (app nomades/vanlifers), Naïa (monde 3D IA open world), "
        "Hub IA (12 agents autonomes). "
        "Vision : rendre l'IA et la tech accessible aux créateurs indépendants et nomades. "
        "Emilie est ouverte à tout domaine : apps, jeux, robotique, hardware, IA, SaaS, B2B. "
        "Critère principal : y a-t-il un marché réel et peut-on construire ça ?"
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

    system = """Tu es analyste produit pour ALNUA. Tu lis des avis négatifs sur des apps concurrentes.
Tu extrais des leçons concrètes pour éviter les mêmes erreurs.

FORMAT de réponse :
===ANTI_PATTERNS===
- [Produit ALNUA concerné] Ce qu'il ne faut PAS faire : explication courte
(liste des erreurs à éviter)

===OPPORTUNITES===
- [Produit ALNUA concerné] Ce que les users réclament et que personne ne fait bien : explication
(liste des opportunités de différenciation)

===PRIORITES===
Top 3 insights les plus actionnables pour ALNUA, classés par impact."""

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
        "nomad remote worker tools indie game market 2026",
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


# ---------------------------------------------------------------------------
# ÉTAPE 2 — Générer des idées (sans bride)
# ---------------------------------------------------------------------------

def _generate_ideas(market_obs: str, user_feedback: str, vision: str, existing_titles: list[str]) -> list[dict]:
    """
    Génère 5-8 idées nouvelles.
    Aucune limite de domaine. Créativité maximale.
    """
    existing = "\n".join(f"- {t}" for t in existing_titles[-20:]) if existing_titles else "Aucune"

    system = """Tu es le centre R&D d'ALNUA, une société tech dirigée par une solopreneuse nomade.
Ta mission : générer des idées de produits innovants et réalistes.

RÈGLES :
- Aucune limite de domaine : app mobile, jeu vidéo, robotique, hardware, SaaS B2B, IA, tool pour créateurs...
- Chaque idée doit avoir un marché réel identifiable
- Pense à ce qu'une solopreneuse peut construire avec des agents IA
- Sois ambitieux mais pas irréaliste
- Évite les idées déjà listées dans "existantes"
- IMPORTANT : les observations marché contiennent les anti-patterns des concurrents — utilise-les pour proposer des idées qui évitent ces erreurs et comblent ces manques

FORMAT de réponse — liste JSON d'objets :
[
  {
    "title": "Nom court du produit",
    "domain": "app|jeu|robotique|hardware|saas|ia|autre",
    "elevator_pitch": "Description en 2 phrases max — problème résolu + marché cible",
    "why_now": "Pourquoi 2026 est le bon moment",
    "effort": "S|M|L|XL"
  }
]

Génère exactement 6 idées variées. Réponds UNIQUEMENT avec le JSON."""

    user = f"""VISION ALNUA :
{vision}

OBSERVATIONS MARCHÉ :
{market_obs[:2000] if market_obs else "Non disponible"}

FEEDBACK UTILISATEURS :
{user_feedback[:1000] if user_feedback else "Non disponible"}

IDÉES DÉJÀ EXISTANTES (ne pas répéter) :
{existing}

Génère 6 idées nouvelles et variées."""

    try:
        raw = _llm(system, user, max_tokens=3000)
        # Parse JSON
        import re
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            ideas_raw = json.loads(match.group())
            ideas = []
            for idea in ideas_raw:
                ideas.append({
                    "id": f"idea_{int(datetime.now().timestamp())}_{len(ideas)}",
                    "title": idea.get("title", "")[:100],
                    "domain": idea.get("domain", "autre"),
                    "description": idea.get("elevator_pitch", ""),
                    "why_now": idea.get("why_now", ""),
                    "effort": idea.get("effort", "M"),
                    "source": "rnd_agent",
                    "status": "pending_evaluation",
                    "score": None,
                    "created_at": datetime.now().isoformat(),
                })
            return ideas
    except Exception as exc:
        logger.warning("rnd_center: generate_ideas failed: %s", exc)
    return []


# ---------------------------------------------------------------------------
# ÉTAPE 3 — Évaluer et scorer
# ---------------------------------------------------------------------------

def _evaluate_idea(idea: dict, vision: str) -> dict:
    """Score une idée sur 3 axes : marché, faisabilité ALNUA, alignement vision."""
    system = """Tu es un analyste produit et business pour ALNUA.
Tu évalues une idée sur 3 critères, chacun noté de 1 à 10.

Réponds UNIQUEMENT en JSON :
{
  "market_score": 7,
  "feasibility_score": 8,
  "vision_score": 6,
  "total": 21,
  "verdict": "GO|MAYBE|NO",
  "reasoning": "Justification en 2 phrases",
  "next_step": "Action concrète recommandée"
}

Critères :
- market_score : taille et accessibilité du marché (10 = marché énorme et accessible)
- feasibility_score : peut-on construire ça avec des agents IA et peu de ressources ? (10 = très faisable)
- vision_score : alignement avec la vision nomade/créateur/indépendant d'ALNUA (10 = parfait fit)
- verdict : GO si total >= 21, MAYBE si 15-20, NO si < 15"""

    user = f"""VISION ALNUA : {vision[:500]}

IDÉE À ÉVALUER :
Titre : {idea['title']}
Domaine : {idea.get('domain', '?')}
Description : {idea.get('description', '')}
Pourquoi maintenant : {idea.get('why_now', '')}
Effort estimé : {idea.get('effort', 'M')}

Évalue cette idée."""

    try:
        raw = _llm(system, user, max_tokens=1500)
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            evaluation = json.loads(match.group())
            idea.update({
                "score": evaluation.get("total", 0),
                "market_score": evaluation.get("market_score", 0),
                "feasibility_score": evaluation.get("feasibility_score", 0),
                "vision_score": evaluation.get("vision_score", 0),
                "verdict": evaluation.get("verdict", "MAYBE"),
                "reasoning": evaluation.get("reasoning", ""),
                "next_step": evaluation.get("next_step", ""),
                "status": "evaluated",
            })
    except Exception as exc:
        logger.warning("rnd_center: evaluate_idea failed for '%s': %s", idea['title'], exc)
        idea["status"] = "evaluation_failed"

    return idea


# ---------------------------------------------------------------------------
# ÉTAPE 4 — Prototyper les meilleures idées
# ---------------------------------------------------------------------------

def _prototype_idea(idea: dict) -> str:
    """
    Pour les idées GO avec effort S ou M :
    - Génère une mini-spec (1 page)
    - Crée un ticket GitHub si c'est une amélioration produit existant
    - Sauvegarde le concept doc dans data/rnd_concepts/
    """
    concepts_dir = Path(os.getenv("HUB_REPO_PATH", "C:/Dev/ALUNA_HUB")) / "data" / "rnd_concepts"
    concepts_dir.mkdir(parents=True, exist_ok=True)

    system = """Tu es le spec agent du centre R&D ALNUA.
Tu rédiges une mini-spec d'une page pour une idée produit.
Format Markdown. Sections : Problème | Solution | Utilisateurs cibles | Features MVP | Stack technique | Métriques de succès | Risques principaux."""

    user = f"""Rédige la mini-spec pour :

Titre : {idea['title']}
Domaine : {idea.get('domain', '?')}
Description : {idea.get('description', '')}
Pourquoi maintenant : {idea.get('why_now', '')}
Effort : {idea.get('effort', 'M')}
Score : {idea.get('score', 0)}/30

Sois concis, concret et actionnable."""

    try:
        spec = _llm(system, user, max_tokens=2000)
        slug = "".join(c if c.isalnum() else "_" for c in idea['title'].lower())[:40]
        date = datetime.now().strftime("%Y%m%d")
        spec_file = concepts_dir / f"{date}_{slug}.md"
        spec_file.write_text(
            f"# {idea['title']}\n\n"
            f"**Domaine :** {idea.get('domain', '?')} | **Score :** {idea.get('score', 0)}/30 | "
            f"**Effort :** {idea.get('effort', 'M')}\n\n"
            f"---\n\n{spec}",
            encoding="utf-8",
        )
        logger.info("rnd_center: spec créée → %s", spec_file.name)
        return str(spec_file)
    except Exception as exc:
        logger.warning("rnd_center: prototype_idea failed: %s", exc)
        return ""


# ---------------------------------------------------------------------------
# ÉTAPE 5 — Rapport hebdomadaire
# ---------------------------------------------------------------------------

def _build_report(new_ideas: list[dict], prototyped: list[str], cycle_date: str) -> str:
    go_ideas = [i for i in new_ideas if i.get("verdict") == "GO"]
    maybe_ideas = [i for i in new_ideas if i.get("verdict") == "MAYBE"]
    no_ideas = [i for i in new_ideas if i.get("verdict") == "NO"]

    lines = [
        f"🧪 Rapport R&D ALNUA — {cycle_date}",
        f"{'='*40}",
        f"",
        f"📊 {len(new_ideas)} idées analysées ce cycle",
        f"✅ GO : {len(go_ideas)} | 🤔 MAYBE : {len(maybe_ideas)} | ❌ NO : {len(no_ideas)}",
        f"",
    ]

    if go_ideas:
        lines.append("🚀 IDÉES GO — À explorer en priorité :")
        for idea in go_ideas[:3]:
            lines.append(
                f"\n• [{idea.get('domain', '?').upper()}] {idea['title']} (score {idea.get('score', '?')}/30)"
            )
            lines.append(f"  {idea.get('description', '')[:120]}")
            lines.append(f"  → {idea.get('next_step', '')[:100]}")

    if prototyped:
        lines.append(f"\n📄 {len(prototyped)} spec(s) rédigée(s) → data/rnd_concepts/")

    lines.append("\n🔍 Analyse concurrentielle complète → data/rnd_competitive/")

    if maybe_ideas:
        lines.append(f"\n🤔 MAYBE — À reconsidérer plus tard :")
        for idea in maybe_ideas[:3]:
            lines.append(f"  • {idea['title']} — {idea.get('reasoning', '')[:80]}")

    lines.append(f"\n💡 Pour injecter une idée : dis au COO 'explore l'idée de...'")
    lines.append(f"🎯 Pour changer le focus : dis au COO 'change le fil conducteur R&D vers...'")

    return "\n".join(lines)


async def _send_telegram(message: str) -> None:
    try:
        from telegram import Bot
        token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        if not token or not chat_id:
            return
        bot = Bot(token=token)
        # Découpe si > 4096 chars (limite Telegram)
        text = message[:4096]
        await bot.send_message(chat_id=int(chat_id), text=text)
    except Exception as exc:
        logger.warning("rnd_center: telegram failed: %s", exc)


# ---------------------------------------------------------------------------
# CYCLE PRINCIPAL
# ---------------------------------------------------------------------------

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


def get_top_ideas(limit: int = 5, verdict: str | None = None) -> list[dict]:
    """Retourne les meilleures idées du journal R&D. Utile pour le COO."""
    try:
        from services.rnd_repository import get_rnd_repository
        api_ideas = get_rnd_repository().get_top_ideas(limit=limit, verdict=verdict)
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
                    "created_at": i.created_at,
                    "evaluated_at": i.evaluated_at,
                }
                for i in api_ideas
            ]
    except Exception as exc:
        logger.warning("rnd_center: get_top_ideas via repository failed: %s", exc)

    ideas = _load_ideas()
    if verdict:
        ideas = [i for i in ideas if i.get("verdict") == verdict.upper()]
    return sorted(ideas, key=lambda x: x.get("score") or 0, reverse=True)[:limit]


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
