"""Fast public-web search for Nadia Live. Hard timeout, no hanging DuckDuckGo client."""

from __future__ import annotations

import json
import logging
import os
import re
import threading
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

USER_AGENT = "ALNUA-Hub/1.0 (live-web-search)"
HTTP_TIMEOUT = 8
BUDGET_SECONDS = 10


def search_fast(query: str, max_results: int = 6) -> list[dict[str, Any]]:
    """Return hits within BUDGET_SECONDS. Empty list on timeout or failure — never hang."""
    holder: list[list[dict[str, Any]]] = [[]]

    def _run() -> None:
        try:
            holder[0] = _search_now(query, max_results)
        except Exception as exc:
            logger.warning("live_web_search failed: %s", type(exc).__name__)

    thread = threading.Thread(target=_run, daemon=True, name="live-web-search")
    thread.start()
    thread.join(BUDGET_SECONDS)
    return holder[0][:max_results]


def _search_now(query: str, max_results: int) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    seen: set[str] = set()
    tavily_key = os.getenv("TAVILY_API_KEY", "").strip()
    if tavily_key:
        hits.extend(_tavily(query, max_results, tavily_key))
    if len(hits) < 4:
        hits.extend(_google_news(query))
    if len(hits) < 4:
        hits.extend(_duckduckgo(query))
    if len(hits) < 3:
        hits.extend(_wikipedia(query))
    out: list[dict[str, Any]] = []
    for hit in hits:
        url = str(hit.get("url") or "")
        if url and url in seen:
            continue
        if url:
            seen.add(url)
        title = str(hit.get("title") or "").strip()
        if not title and not url:
            continue
        out.append(
            {
                "title": title[:160],
                "url": url[:300],
                "content": str(hit.get("content") or "")[:400],
            }
        )
        if len(out) >= max_results:
            break
    return out


def _tavily(query: str, max_results: int, api_key: str) -> list[dict[str, Any]]:
    payload = json.dumps(
        {
            "api_key": api_key,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
            "include_answer": True,
        }
    ).encode()
    req = Request(
        "https://api.tavily.com/search",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(req, timeout=HTTP_TIMEOUT) as resp:  # noqa: S310 — Tavily
            data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        logger.warning("tavily live search: %s", type(exc).__name__)
        return []
    rows = []
    answer = str(data.get("answer") or "").strip()
    for item in data.get("results") or []:
        if not isinstance(item, dict):
            continue
        rows.append(
            {
                "title": item.get("title") or "",
                "url": item.get("url") or "",
                "content": item.get("content") or answer,
            }
        )
    return rows


def _google_news(query: str) -> list[dict[str, Any]]:
    url = (
        "https://news.google.com/rss/search?q="
        f"{quote(query)}&hl=fr&gl=FR&ceid=FR:fr"
    )
    xml = _get_text(url)
    if not xml:
        return []
    rows: list[dict[str, Any]] = []
    for block in re.findall(r"<item>(.*?)</item>", xml, flags=re.DOTALL | re.IGNORECASE):
        title = _rss_tag(block, "title")
        link = _rss_tag(block, "link")
        desc = _strip_html(_rss_tag(block, "description"))
        if not title:
            continue
        rows.append({"title": title[:160], "url": link[:300], "content": desc[:400]})
        if len(rows) >= 6:
            break
    return rows


def _rss_tag(block: str, name: str) -> str:
    match = re.search(
        rf"<{name}[^>]*>(.*?)</{name}>",
        block,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if not match:
        return ""
    inner = match.group(1).replace("<![CDATA[", "").replace("]]>", "")
    return _strip_html(inner).strip()


def _duckduckgo(query: str) -> list[dict[str, Any]]:
    url = (
        "https://api.duckduckgo.com/?q="
        f"{quote(query)}&format=json&no_html=1&skip_disambig=1&no_redirect=1"
    )
    data = _get_json(url)
    if not data:
        return []
    rows: list[dict[str, Any]] = []
    abstract = str(data.get("AbstractText") or "").strip()
    abs_url = str(data.get("AbstractURL") or "")
    heading = str(data.get("Heading") or query)
    if abstract:
        rows.append({"title": heading, "url": abs_url, "content": abstract})
    for topic in data.get("RelatedTopics") or []:
        rows.extend(_ddg_topic(topic))
    for item in data.get("Results") or []:
        if isinstance(item, dict) and item.get("FirstURL"):
            rows.append(
                {
                    "title": _strip_html(str(item.get("Text") or item["FirstURL"])),
                    "url": str(item["FirstURL"]),
                    "content": "",
                }
            )
    return rows


def _ddg_topic(topic: Any) -> list[dict[str, Any]]:
    if isinstance(topic, dict) and "Topics" in topic:
        rows: list[dict[str, Any]] = []
        for child in topic.get("Topics") or []:
            rows.extend(_ddg_topic(child))
        return rows
    if not isinstance(topic, dict):
        return []
    first = str(topic.get("FirstURL") or "")
    text = _strip_html(str(topic.get("Text") or ""))
    if not first:
        return []
    return [{"title": text[:120] or first, "url": first, "content": text}]


def _wikipedia(query: str) -> list[dict[str, Any]]:
    url = (
        "https://fr.wikipedia.org/w/api.php?action=query&list=search"
        f"&srsearch={quote(query)}&utf8=1&format=json&srlimit=5"
    )
    data = _get_json(url)
    pages = ((data.get("query") or {}).get("search") or []) if data else []
    rows: list[dict[str, Any]] = []
    for page in pages:
        if not isinstance(page, dict):
            continue
        title = str(page.get("title") or "")
        snippet = _strip_html(str(page.get("snippet") or ""))
        if not title:
            continue
        slug = quote(title.replace(" ", "_"))
        rows.append(
            {
                "title": title,
                "url": f"https://fr.wikipedia.org/wiki/{slug}",
                "content": snippet,
            }
        )
    return rows


def _get_json(url: str) -> dict[str, Any]:
    text = _get_text(url)
    if not text:
        return {}
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        return {}
    return raw if isinstance(raw, dict) else {}


def _get_text(url: str) -> str:
    req = Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(req, timeout=HTTP_TIMEOUT) as resp:  # noqa: S310 — HTTPS news / wiki / DDG
            return resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        logger.warning("live_web_search GET failed: %s", type(exc).__name__)
        return ""


def _strip_html(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text).replace("&quot;", '"').strip()
