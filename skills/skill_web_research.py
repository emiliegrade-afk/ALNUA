"""
skill_web_research.py — Veille web autonome par domaine.

Chaque agent a ses topics de recherche.
Toutes les semaines (ou sur demande du COO), il cherche sur le web,
distille les infos clés et les écrit dans sa propre Mem0.

Exemples :
    - hardware_agent recherche "ESP32 2026", "new GPU benchmarks"
    - marketing_agent recherche "TikTok algorithm update", "Instagram growth"
    - dev_app recherche "FastAPI new features", "Python security patches"

Usage :
    from skills.skill_web_research import research_domain, teach_agent
    research_domain("marketing_agent")          # recherche auto selon ses topics
    teach_agent("marketing_agent", "Les Reels courtes < 30s ont +40% de reach en 2026")
    research_domain("hardware_agent", topic="RISC-V 2026")  # topic custom
"""
from __future__ import annotations

import json
import logging
import os
import threading
import urllib.parse
import urllib.request
from datetime import datetime

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"
RESEARCH_MODEL = os.getenv("RESEARCH_MODEL", "openrouter/minimax/minimax-m1")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")  # optionnel — DuckDuckGo si absent


# ---------------------------------------------------------------------------
# Topics de veille par agent — ce que chaque agent surveille chaque semaine
# ---------------------------------------------------------------------------

AGENT_RESEARCH_TOPICS: dict[str, list[str]] = {
    "dev_app": [
        "FastAPI latest features 2026",
        "Python security vulnerabilities patch",
        "Supabase new features changelog",
        "CrewAI agent framework updates",
    ],
    "dev_gaming": [
        "Unreal Engine 5 update 2026",
        "game development best practices 2026",
        "indie game engine comparison 2026",
        "procedural generation techniques",
    ],
    "embedded_dev": [
        "ESP32 new firmware 2026",
        "RISC-V microcontroller 2026",
        "embedded Linux best practices",
        "IoT security 2026",
    ],
    "hardware_agent": [
        "GPU benchmark comparison 2026",
        "new CPU architecture 2026",
        "AI hardware accelerator 2026",
        "PCB design tools update",
    ],
    "marketing_agent": [
        "TikTok algorithm update 2026",
        "Instagram Reels growth strategy 2026",
        "LinkedIn B2B marketing tactics 2026",
        "growth hacking indie app 2026",
    ],
    "content_agent": [
        "content marketing trends 2026",
        "SEO strategy update 2026",
        "viral content formats 2026",
        "storytelling technique brand 2026",
    ],
    "accountant_agent": [
        "French accounting regulations 2026",
        "startup tax optimization France",
        "SaaS revenue recognition rules",
        "freelance micro-entrepreneur TVA 2026",
    ],
    "game_director": [
        "game design trends 2026",
        "player engagement mechanics 2026",
        "narrative game design techniques",
        "indie game monetization strategy",
    ],
    "rnd_agent": [
        "AI agent self-improvement research 2026",
        "multi-agent system architecture",
        "LLM fine-tuning techniques 2026",
        "autonomous AI systems research",
    ],
    "coo": [
        "AI startup operations best practices",
        "solopreneur productivity systems 2026",
        "AI company management automation",
    ],
    "pm_agent": [
        "agile project management AI tools 2026",
        "indie startup sprint planning",
        "product roadmap prioritization framework",
    ],
    "qa_agent": [
        "Python testing best practices 2026",
        "automated QA AI tools",
        "software quality metrics 2026",
    ],
    "spec_agent": [
        "software architecture patterns 2026",
        "API design best practices",
        "technical specification writing AI",
    ],
}


# ---------------------------------------------------------------------------
# Moteur de recherche — Tavily si dispo, sinon DuckDuckGo
# ---------------------------------------------------------------------------

def _search_tavily(query: str, max_results: int = 5) -> list[dict]:
    """Recherche via Tavily API (meilleure qualité pour agents)."""
    payload = json.dumps({
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "basic",
        "max_results": max_results,
        "include_answer": True,
    }).encode()
    req = urllib.request.Request(
        "https://api.tavily.com/search",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            return data.get("results", [])
    except Exception as exc:
        logger.warning("Tavily search failed: %s", exc)
        return []


def _search_duckduckgo(query: str, max_results: int = 5) -> list[dict]:
    """Recherche via DuckDuckGo (gratuit, aucune clé requise)."""
    try:
        from ddgs import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "content": r.get("body", ""),
                })
        return results
    except ImportError:
        logger.warning("ddgs non installé — pip install ddgs")
        return []
    except Exception as exc:
        logger.warning("DuckDuckGo search failed: %s", exc)
        return []


def _search(query: str, max_results: int = 5) -> list[dict]:
    """Utilise Tavily si configuré, sinon DuckDuckGo."""
    if TAVILY_API_KEY:
        return _search_tavily(query, max_results)
    return _search_duckduckgo(query, max_results)


# ---------------------------------------------------------------------------
# Distillation — LLM transforme les résultats bruts en leçons actionnables
# ---------------------------------------------------------------------------

def _distill_research(agent_id: str, topic: str, raw_results: list[dict]) -> str:
    """
    Le LLM lit les résultats de recherche et distille 2-3 points clés
    pertinents pour le domaine de l'agent.
    """
    if not raw_results:
        return ""

    results_text = "\n\n".join(
        f"Source: {r.get('title', '')}\n{r.get('content', '')[:400]}"
        for r in raw_results[:5]
    )

    system = f"""Tu es l'agent {agent_id} d'ALNUA.
Tu lis des résultats de recherche sur "{topic}" et tu retiens ce qui pourrait servir
aujourd'hui ou plus tard — rien ne doit être ignoré.
Si le contenu le permet, développe un peu plus (faits, chiffres) —
jusqu'à ~8 lignes utiles. Format puces.
Format : "• [point clé et quand ça pourrait servir]"
Si le contenu est faible, résume quand même en 1 bullet "à garder pour plus tard"."""

    user = f"""Résultats de recherche sur : {topic}

{results_text}

Qu'est-ce qui est vraiment utile à retenir pour ton travail ?"""

    payload = json.dumps({
        "model": RESEARCH_MODEL.replace("openrouter/", ""),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 900,
    }).encode()

    req = urllib.request.Request(
        OPENROUTER_BASE,
        data=payload,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            content = json.loads(r.read())["choices"][0]["message"]["content"]
            return content.strip() if content else ""
    except Exception as exc:
        logger.warning("Research distill failed: %s", exc)
        return ""


# ---------------------------------------------------------------------------
# Points d'entrée principaux
# ---------------------------------------------------------------------------

def research_domain(
    agent_id: str,
    topic: str | None = None,
    blocking: bool = False,
) -> None:
    """
    Lance la veille web d'un agent sur son domaine.
    Si topic est fourni, recherche ce topic spécifique.
    Sinon, parcourt tous les topics configurés pour cet agent.

    Non-bloquant par défaut — tourne en daemon thread.
    """
    def _run():
        topics = [topic] if topic else AGENT_RESEARCH_TOPICS.get(agent_id, [])
        if not topics:
            logger.info("research_domain: aucun topic configuré pour %s", agent_id)
            return

        from skills.skill_mem0 import remember
        date = datetime.now().strftime("%Y-%m-%d")
        total_learned = 0

        for t in topics:
            logger.info("research_domain: %s recherche '%s'", agent_id, t)
            results = _search(t, max_results=5)
            if not results:
                continue

            lesson = _distill_research(agent_id, t, results)
            if not lesson:
                lesson = f"• Source archivée — à relire plus tard ({t})"

            memory_entry = f"[Recherche {date}] {t} :\n{lesson}"
            remember(memory_entry, agent_id=agent_id)

            try:
                from services.bureau_library import add_entry, bureau_for_agent

                # summary = short UI card; digest = full distilled research (no truncation loss)
                short = lesson if len(lesson) <= 400 else (lesson[:397] + "...")
                add_entry(
                    bureau=bureau_for_agent(agent_id),
                    title=t[:200],
                    summary=short,
                    digest=lesson,
                    timing="later",
                    source_url=str(results[0].get("url") or ""),
                    source_title=str(results[0].get("title") or t),
                    topics=[t],
                    agent_id=agent_id,
                    requested_by="scheduler",
                    query=t,
                )
            except Exception:
                pass

            total_learned += 1
            logger.info("research_domain: %s — leçon enregistrée pour '%s'", agent_id, t)

        if total_learned > 0:
            logger.info(
                "research_domain: %s — %d leçon(s) enregistrée(s) ce cycle",
                agent_id, total_learned,
            )

    if blocking:
        _run()
    else:
        threading.Thread(target=_run, daemon=True).start()


def teach_agent(agent_id: str, content: str, source: str = "manual") -> None:
    """
    Pousse une leçon directement dans la mémoire d'un agent.
    Utilisé par : toi (via COO), ou par un autre agent qui partage une découverte.

    Exemples :
        teach_agent("marketing_agent", "Les Reels < 30s ont +40% de reach selon Meta Q1 2026")
        teach_agent("hardware_agent", "Le Raspberry Pi 6 sort en septembre 2026")
    """
    try:
        from skills.skill_mem0 import remember
        date = datetime.now().strftime("%Y-%m-%d")
        entry = f"[Leçon externe {date} — source: {source}] {content}"
        remember(entry, agent_id=agent_id)
        logger.info("teach_agent: leçon injectée pour %s", agent_id)
    except Exception as exc:
        logger.warning("teach_agent failed for %s: %s", agent_id, exc)


def research_all_agents(blocking: bool = False) -> None:
    """
    Lance la veille pour tous les agents configurés.
    Appelé par le scheduler hebdomadaire.
    """
    def _run():
        for agent_id in AGENT_RESEARCH_TOPICS:
            research_domain(agent_id, blocking=True)
            import time
            time.sleep(2)  # évite de spammer l'API de recherche

    if blocking:
        _run()
    else:
        threading.Thread(target=_run, daemon=True).start()
