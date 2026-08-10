"""Trend monitor — fetchers for HN, Reddit, GitHub."""

from __future__ import annotations

import json
import logging
import time
import urllib.request
from datetime import datetime, timedelta, timezone

from services.trend_monitor_models import TrendItem

logger = logging.getLogger(__name__)


def http_get(url: str, timeout: int = 10) -> dict | list | None:
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
    ids = http_get(stories_url)
    if not ids or not isinstance(ids, list):
        return []

    items: list[TrendItem] = []
    for story_id in ids[:limit]:
        data = http_get(f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json")
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
    data = http_get(url)
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
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")

    query = f"created:>{cutoff}"
    if language:
        query += f" language:{language}"

    url = (
        f"https://api.github.com/search/repositories"
        f"?q={urllib.request.quote(query)}&sort=stars&order=desc&per_page={limit}"
    )
    data = http_get(url)
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
