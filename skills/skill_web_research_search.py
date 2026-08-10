"""Search and distill helpers for agent web research."""

from __future__ import annotations

import json
import logging
import os
import urllib.request

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE = "https://openrouter.ai/api/v1/chat/completions"
RESEARCH_MODEL = os.getenv("RESEARCH_MODEL", "openrouter/minimax/minimax-m1")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


def search_tavily(query: str, max_results: int = 5) -> list[dict]:
    """Recherche via Tavily API (meilleure qualité pour agents)."""
    payload = json.dumps(
        {
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
            "include_answer": True,
        }
    ).encode()
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


def search_duckduckgo(query: str, max_results: int = 5) -> list[dict]:
    """Recherche via DuckDuckGo (gratuit, aucune clé requise)."""
    try:
        from ddgs import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append(
                    {
                        "title": r.get("title", ""),
                        "url": r.get("href", ""),
                        "content": r.get("body", ""),
                    }
                )
        return results
    except ImportError:
        logger.warning("ddgs non installé — pip install ddgs")
        return []
    except Exception as exc:
        logger.warning("DuckDuckGo search failed: %s", exc)
        return []


def search(query: str, max_results: int = 5) -> list[dict]:
    """Utilise Tavily si configuré, sinon DuckDuckGo."""
    if TAVILY_API_KEY:
        return search_tavily(query, max_results)
    return search_duckduckgo(query, max_results)


def distill_research(agent_id: str, topic: str, raw_results: list[dict]) -> str:
    """
    Le LLM lit les résultats de recherche et distille 2-3 points clés
    pertinents pour le domaine de l'agent.
    """
    if not raw_results:
        return ""

    results_text = "\n\n".join(
        f"Source: {r.get('title', '')}\n{r.get('content', '')[:400]}" for r in raw_results[:5]
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

    payload = json.dumps(
        {
            "model": RESEARCH_MODEL.replace("openrouter/", ""),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": 0.2,
            "max_tokens": 900,
        }
    ).encode()

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
