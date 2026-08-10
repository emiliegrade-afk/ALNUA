"""Library vault export — topic slug normalization."""

from __future__ import annotations

import re
from typing import Any

_STOP = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "for",
        "to",
        "in",
        "on",
        "with",
        "de",
        "du",
        "des",
        "le",
        "la",
        "les",
        "un",
        "une",
        "et",
        "ou",
        "pour",
        "par",
        "sur",
        "dans",
        "avec",
        "qui",
        "que",
        "au",
        "aux",
        "en",
        "latest",
        "update",
        "updates",
        "new",
        "features",
        "2024",
        "2025",
        "2026",
        "2027",
    }
)


def slugify_topic(raw: str) -> str:
    """Normalize a topic / query string into a stable catalog slug."""
    text = (raw or "").strip().lower()
    text = re.sub(r"[^\w\s\-]+", " ", text, flags=re.UNICODE)
    words = [w for w in re.split(r"[\s_\-]+", text) if w and w not in _STOP and len(w) > 1]
    if not words:
        words = [w for w in re.split(r"[\s_\-]+", text) if w][:4] or ["general"]
    slug = "-".join(words[:6])
    return slug[:80].strip("-") or "general"


def normalize_topics(entry: dict[str, Any]) -> list[str]:
    """Return unique topic slugs for an entry (from topics list + query fallback)."""
    slugs: list[str] = []
    seen: set[str] = set()
    raw_topics = entry.get("topics") or []
    if isinstance(raw_topics, list):
        for t in raw_topics:
            slug = slugify_topic(str(t))
            if slug and slug not in seen:
                seen.add(slug)
                slugs.append(slug)
    query = str(entry.get("query") or "").strip()
    if query:
        slug = slugify_topic(query)
        if slug and slug not in seen:
            seen.add(slug)
            slugs.append(slug)
    if not slugs:
        title_slug = slugify_topic(str(entry.get("title") or "general"))
        slugs.append(title_slug)
    return slugs[:8]
