"""
Topic catalog — scannable index of library subjects for on-demand agent learning.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from services.library_vault_export import (
    CATALOG_FILE,
    export_library_to_vault,
    load_catalog,
    normalize_topics,
    save_catalog,
    slugify_topic,
)
from services.bureau_library import _load_store

logger = logging.getLogger(__name__)


def list_topics(
    *,
    query: str = "",
    bureau: str | None = None,
    timing_now_only: bool = False,
    limit: int = 40,
    offset: int = 0,
) -> dict[str, Any]:
    catalog = load_catalog()
    topics = list((catalog.get("topics") or {}).values())

    if bureau:
        topics = [t for t in topics if bureau in (t.get("bureaus") or [])]
    if timing_now_only:
        topics = [t for t in topics if t.get("has_now")]

    q = (query or "").strip().lower()
    if q:
        tokens = [tok for tok in re.split(r"\s+", q) if tok]
        scored: list[tuple[int, dict[str, Any]]] = []
        for row in topics:
            blob = " ".join(
                [
                    str(row.get("slug") or ""),
                    str(row.get("label") or ""),
                    " ".join(row.get("titles") or []),
                    " ".join(row.get("bureaus") or []),
                ]
            ).lower()
            score = sum(1 for tok in tokens if tok in blob)
            if score > 0 or slugify_topic(q) == row.get("slug"):
                if slugify_topic(q) == row.get("slug"):
                    score += 5
                scored.append((score, row))
        scored.sort(key=lambda x: (-x[0], -len(x[1].get("entry_ids") or [])))
        topics = [r for _, r in scored]
    else:
        topics.sort(
            key=lambda t: (
                -int(t.get("has_now") or 0),
                -int(t.get("learn_count") or 0),
                -len(t.get("entry_ids") or []),
                str(t.get("slug") or ""),
            )
        )

    total = len(topics)
    page = topics[offset : offset + limit]
    return {
        "topics": page,
        "total": total,
        "offset": offset,
        "limit": limit,
        "updated_at": catalog.get("updated_at"),
        "catalog_path": str(CATALOG_FILE),
        "entry_count": catalog.get("entry_count", 0),
        "topic_count": catalog.get("topic_count", 0),
    }


def get_topic(slug: str) -> dict[str, Any] | None:
    catalog = load_catalog()
    key = slugify_topic(slug) if slug else ""
    topics = catalog.get("topics") or {}
    row = topics.get(key) or topics.get(slug)
    if not row:
        # Fuzzy: exact slug match after normalize
        for s, t in topics.items():
            if s == key or slugify_topic(s) == key:
                row = t
                break
    if not row:
        return None

    store = _load_store()
    by_id = {str(e.get("id")): e for e in store.get("entries", [])}
    entries = []
    for eid in row.get("entry_ids") or []:
        e = by_id.get(eid)
        if not e:
            continue
        entries.append(
            {
                "id": e.get("id"),
                "title": e.get("title"),
                "summary": e.get("summary"),
                "digest": e.get("digest"),
                "bureau": e.get("bureau"),
                "timing": e.get("timing"),
                "source_url": e.get("source_url"),
                "topics": normalize_topics(e),
            }
        )

    return {
        **row,
        "entries": entries,
        "digest_path": f"library/_digests/{row.get('slug')}.md",
    }


def increment_learn_count(slug: str) -> dict[str, Any]:
    catalog = load_catalog()
    topics = catalog.setdefault("topics", {})
    key = slugify_topic(slug)
    row = topics.get(key)
    if not row:
        return {"ok": False, "error": "topic_not_found", "slug": key}
    row["learn_count"] = int(row.get("learn_count") or 0) + 1
    topics[key] = row
    catalog["topics"] = topics
    save_catalog(catalog)
    return {"ok": True, "slug": key, "learn_count": row["learn_count"]}


def mark_promoted_skill(slug: str, skill_path: str) -> dict[str, Any]:
    catalog = load_catalog()
    topics = catalog.setdefault("topics", {})
    key = slugify_topic(slug)
    row = topics.get(key)
    if not row:
        return {"ok": False, "error": "topic_not_found", "slug": key}
    row["promoted_skill"] = skill_path
    topics[key] = row
    catalog["topics"] = topics
    save_catalog(catalog)
    return {"ok": True, "slug": key, "promoted_skill": skill_path}


def sync_vault(*, index_chroma: bool = False, limit: int | None = None) -> dict[str, Any]:
    """Re-export library → vault + rebuild catalog."""
    return export_library_to_vault(limit=limit, index_chroma=index_chroma)


def search_topics_for_task(
    task: str,
    *,
    bureau: str | None = None,
    limit: int = 5,
) -> list[dict[str, Any]]:
    """Best topic hits for an agent task (used by learning context injection)."""
    res = list_topics(query=task, bureau=bureau, limit=limit)
    hits = list(res.get("topics") or [])
    if len(hits) < limit and bureau:
        # Fallback: global search if bureau-scoped is thin
        extra = list_topics(query=task, limit=limit)
        seen = {h.get("slug") for h in hits}
        for row in extra.get("topics") or []:
            if row.get("slug") in seen:
                continue
            hits.append(row)
            if len(hits) >= limit:
                break
    return hits[:limit]
