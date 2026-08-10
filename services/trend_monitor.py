"""
services/trend_monitor.py — Agrégateur de tendances multi-plateforme ALNUA.

Inspiré de TrendRadar (sansan0, ⭐59k) — agrège HackerNews, Reddit, GitHub Trending
et génère un brief de tendances pour Camille (Marketing) et le content_pipeline.

Usage:
    from services.trend_monitor import get_trend_brief, aggregate_trends

    # Brief complet pour un domaine
    brief = get_trend_brief(topics=["AI agents", "gaming", "FastAPI"])

    # Agrégation brute sans synthèse LLM
    trends = aggregate_trends(sources=["hn", "reddit", "github"])
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.trend_monitor_fetch import (
    fetch_github_trending,
    fetch_hackernews,
    fetch_multi_reddit,
)
from services.trend_monitor_models import TrendBrief, TrendItem
from services.trend_monitor_synthesis import llm_synthesize_trends

__all__ = [
    "TrendBrief",
    "TrendItem",
    "aggregate_trends",
    "fetch_github_trending",
    "fetch_hackernews",
    "fetch_multi_reddit",
    "get_raw_trends",
    "get_trend_brief",
]


def aggregate_trends(
    sources: list[str] | None = None,
    topics: list[str] | None = None,
    hn_limit: int = 20,
    reddit_subreddits: list[str] | None = None,
    github_language: str = "",
    github_since: str = "daily",
) -> list[TrendItem]:
    """
    Agrège les tendances de toutes les sources demandées.

    sources: ["hn", "reddit", "github"] — None = toutes
    topics: filtrer par mots-clés dans le titre (case-insensitive)
    """
    if sources is None:
        sources = ["hn", "reddit", "github"]

    all_items: list[TrendItem] = []

    if "hn" in sources:
        all_items.extend(fetch_hackernews(limit=hn_limit))

    if "reddit" in sources:
        all_items.extend(fetch_multi_reddit(reddit_subreddits))

    if "github" in sources:
        all_items.extend(fetch_github_trending(github_language, github_since))

    if topics:
        keywords = [t.lower() for t in topics]
        all_items = [
            item for item in all_items
            if any(kw in item.title.lower() for kw in keywords)
        ]

    all_items.sort(key=lambda x: x.score, reverse=True)
    return all_items


def get_trend_brief(
    topics: list[str] | None = None,
    sources: list[str] | None = None,
    reddit_subreddits: list[str] | None = None,
    github_language: str = "",
    agent_id: str = "marketing",
) -> dict[str, Any]:
    """
    Pipeline complet : fetch → filtre → synthèse LLM → TrendBrief.

    Endpoint: POST /services/trends/brief
    Agent principal: Camille (Marketing)
    """
    if topics is None:
        topics = []
    if sources is None:
        sources = ["hn", "reddit", "github"]

    items = aggregate_trends(
        sources=sources,
        topics=topics if topics else None,
        reddit_subreddits=reddit_subreddits,
        github_language=github_language,
    )

    if not items:
        return {
            "error": "Aucune tendance trouvée",
            "topics": topics,
            "sources_used": sources,
            "raw_items": [],
            "synthesis": "",
            "key_signals": [],
            "content_angles": [],
        }

    synthesis_data = llm_synthesize_trends(items, topics, agent_id=agent_id)

    brief = TrendBrief(
        topics=topics,
        sources_used=sources,
        raw_items=items,
        synthesis=synthesis_data.get("synthesis", ""),
        key_signals=synthesis_data.get("key_signals", []),
        content_angles=synthesis_data.get("content_angles", []),
    )

    result = brief.to_dict()
    result.update({
        "urgency": synthesis_data.get("urgency", "this_week"),
        "top_platform": synthesis_data.get("top_platform", "linkedin"),
    })
    return result


def get_raw_trends(
    sources: list[str] | None = None,
    topics: list[str] | None = None,
    limit: int = 30,
) -> dict[str, Any]:
    """
    Agrégation brute sans synthèse LLM. Plus rapide, moins de tokens.

    Endpoint: GET /services/trends/today
    """
    items = aggregate_trends(sources=sources, topics=topics if topics else None)
    return {
        "total": len(items),
        "items": [i.to_dict() for i in items[:limit]],
        "sources": list({i.source for i in items}),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }
