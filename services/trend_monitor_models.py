"""Trend monitor — dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


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
