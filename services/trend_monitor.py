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

import json
import logging
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class TrendItem:
    title: str
    url: str
    source: str           # "hackernews" | "reddit" | "github"
    score: int = 0        # upvotes / stars
    comments: int = 0
    category: str = ""
    fetched_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "source": self.source,
            "score": self.score,
            "comments": self.comments,
            "category": self.category,
            "fetched_at": self.fetched_at,
        }


@dataclass
class TrendBrief:
    topics: list[str]
    sources_used: list[str]
    raw_items: list[TrendItem]
    synthesis: str          # Résumé LLM
    key_signals: list[str]  # 3-5 signaux clés
    content_angles: list[str]  # Angles de contenu suggérés pour Camille/Sofia
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "topics": self.topics,
            "sources_used": self.sources_used,
            "total_items": len(self.raw_items),
            "top_items": [i.to_dict() for i in self.raw_items[:10]],
            "synthesis": self.synthesis,
            "key_signals": self.key_signals,
            "content_angles": self.content_angles,
            "generated_at": self.generated_at,
        }


# ---------------------------------------------------------------------------
# Fetchers — APIs publiques sans authentification
# ---------------------------------------------------------------------------

def _http_get(url: str, timeout: int = 10) -> dict | list | None:
    """Fetch JSON from URL, silently fails on error."""
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "ALNUA-TrendMonitor/1.0 (research bot)"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        logger.warning(f"trend_monitor fetch failed: {url} — {e}")
        return None


def fetch_hackernews(limit: int = 20, story_type: str = "top") -> list[TrendItem]:
    """
    Fetch top/new/best stories from HackerNews.
    story_type: "top" | "new" | "best" | "ask" | "show"
    """
    stories_url = f"https://hacker-news.firebaseio.com/v0/{story_type}stories.json"
    ids = _http_get(stories_url)
    if not ids or not isinstance(ids, list):
        return []

    items: list[TrendItem] = []
    for story_id in ids[:limit]:
        data = _http_get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
        if not data or data.get("type") != "story":
            continue
        items.append(TrendItem(
            title=data.get("title", ""),
            url=data.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
            source="hackernews",
            score=data.get("score", 0),
            comments=data.get("descendants", 0),
        ))
        if len(items) >= limit:
            break
    return items


def fetch_reddit(subreddit: str = "programming", limit: int = 15) -> list[TrendItem]:
    """Fetch hot posts from a subreddit — no auth needed for public subs."""
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    data = _http_get(url)
    if not data:
        return []

    items: list[TrendItem] = []
    try:
        posts = data.get("data", {}).get("children", [])
        for post in posts:
            p = post.get("data", {})
            if p.get("stickied"):
                continue
            items.append(TrendItem(
                title=p.get("title", ""),
                url=f"https://reddit.com{p.get('permalink', '')}",
                source="reddit",
                score=p.get("score", 0),
                comments=p.get("num_comments", 0),
                category=subreddit,
            ))
    except Exception as e:
        logger.warning(f"Reddit parse error r/{subreddit}: {e}")

    return items


def fetch_github_trending(language: str = "", since: str = "daily", limit: int = 10) -> list[TrendItem]:
    """
    Fetch trending repos from GitHub Search API.
    since: "daily" (pushed today) | "weekly" | "monthly"
    """
    days = {"daily": 1, "weekly": 7, "monthly": 30}.get(since, 1)
    from datetime import timedelta
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    query = f"created:>{cutoff}"
    if language:
        query += f" language:{language}"

    url = (
        f"https://api.github.com/search/repositories"
        f"?q={urllib.request.quote(query)}&sort=stars&order=desc&per_page={limit}"
    )
    data = _http_get(url)
    if not data:
        return []

    items: list[TrendItem] = []
    try:
        for repo in data.get("items", []):
            items.append(TrendItem(
                title=f"{repo['full_name']} — {repo.get('description', '')}",
                url=repo.get("html_url", ""),
                source="github",
                score=repo.get("stargazers_count", 0),
                comments=repo.get("forks_count", 0),
                category=repo.get("language", ""),
            ))
    except Exception as e:
        logger.warning(f"GitHub trending parse error: {e}")

    return items


def fetch_multi_reddit(
    subreddits: list[str] | None = None, limit_per_sub: int = 10
) -> list[TrendItem]:
    """Fetch from multiple subreddits relevant to ALNUA."""
    if subreddits is None:
        subreddits = ["gamedev", "artificial", "webdev", "programming", "startups", "marketing"]

    items: list[TrendItem] = []
    for sub in subreddits:
        items.extend(fetch_reddit(sub, limit=limit_per_sub))
        time.sleep(0.5)  # Rate limiting Reddit
    return items


# ---------------------------------------------------------------------------
# Aggregator principal
# ---------------------------------------------------------------------------

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

    # Filtre par topics si spécifiés
    if topics:
        keywords = [t.lower() for t in topics]
        all_items = [
            item for item in all_items
            if any(kw in item.title.lower() for kw in keywords)
        ]

    # Trier par score décroissant
    all_items.sort(key=lambda x: x.score, reverse=True)
    return all_items


# ---------------------------------------------------------------------------
# LLM Synthesis
# ---------------------------------------------------------------------------

def _llm_synthesize_trends(items: list[TrendItem], topics: list[str], agent_id: str = "marketing") -> dict[str, Any]:
    """Utilise LLMClient pour générer un brief de tendances."""
    try:
        from agents.base import LLMClient
        llm = LLMClient()

        top_items_text = "\n".join([
            f"- [{item.source.upper()}] {item.title} (score: {item.score})"
            for item in items[:20]
        ])

        topics_str = ", ".join(topics) if topics else "général"

        system = """Tu es Camille Rousseau, responsable Marketing d'ALNUA.
Tu analyses les tendances du marché pour identifier des opportunités de contenu.
Réponds en JSON valide structuré."""

        prompt = f"""Analyse ces {len(items)} tendances actuelles pour les topics : {topics_str}

TOP TENDANCES :
{top_items_text}

Génère un brief JSON avec :
- synthesis (string): résumé en 2-3 phrases des trends dominantes
- key_signals (list[string]): 3-5 signaux clés à retenir (chacun < 15 mots)
- content_angles (list[string]): 3-5 angles de contenu exploitables pour ALNUA (posts, articles, social)
- urgency (string): "now" | "this_week" | "this_month" selon l'opportunité
- top_platform (string): meilleure plateforme pour capitaliser sur ces trends"""

        raw = llm.complete(system, prompt, agent_id=agent_id, temperature=0.3)

        from agents.base import parse_json_response
        return parse_json_response(raw)
    except Exception as e:
        logger.warning(f"LLM synthesis failed: {e}")
        return {
            "synthesis": "Synthèse indisponible (LLM error).",
            "key_signals": [item.title for item in items[:3]],
            "content_angles": [],
            "urgency": "this_week",
            "top_platform": "linkedin",
        }


# ---------------------------------------------------------------------------
# API principale
# ---------------------------------------------------------------------------

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

    # Fetch & aggregate
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

    # LLM synthesis
    synthesis_data = _llm_synthesize_trends(items, topics, agent_id=agent_id)

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
