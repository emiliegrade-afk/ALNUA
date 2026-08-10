"""CRUD and listing for bureau library entries."""
from __future__ import annotations

import logging
import uuid
from typing import Any

from services.bureau_library_constants import (
    AGENT_TO_BUREAU,
    BUREAU_LABELS,
    DEFAULT_AGENT_BY_BUREAU,
    VALID_BUREAUS,
    Timing,
)
from services.bureau_library_store import _load_store, _save_store, _utc_now

logger = logging.getLogger(__name__)


def bureau_for_agent(agent_id: str | None) -> str:
    if not agent_id:
        return "hub"
    return AGENT_TO_BUREAU.get(agent_id, AGENT_TO_BUREAU.get(agent_id.replace("_agent", ""), "hub"))


def default_agent_for_bureau(bureau: str) -> str:
    return DEFAULT_AGENT_BY_BUREAU.get(bureau, "coo")


def add_entry(
    *,
    bureau: str,
    title: str,
    summary: str,
    timing: Timing = "later",
    source_url: str = "",
    source_title: str = "",
    topics: list[str] | None = None,
    agent_id: str = "",
    requested_by: str = "ceo",
    query: str = "",
    digest: str = "",
) -> dict[str, Any]:
    bureau = bureau if bureau in VALID_BUREAUS else "hub"
    entry = {
        "id": str(uuid.uuid4()),
        "bureau": bureau,
        "title": title[:300],
        "summary": summary[:4000],
        "digest": (digest or "")[:12000],
        "timing": timing if timing in ("now", "later") else "later",
        "source_url": source_url[:2000],
        "source_title": source_title[:300],
        "topics": (topics or [])[:12],
        "agent_id": agent_id,
        "requested_by": requested_by,
        "query": query[:500],
        "created_at": _utc_now(),
    }
    store = _load_store()
    store["entries"].append(entry)
    _save_store(store)

    try:
        from services.team_enrichment import fanout_library_entry

        fanout_library_entry(entry, distill_lessons=entry["timing"] == "now")
    except Exception as exc:
        logger.debug("library fanout skipped: %s", exc)

    try:
        from services.library_vault_export import export_entry_to_vault

        export_entry_to_vault(entry, update_catalog=True)
    except Exception as exc:
        logger.debug("library vault export skipped: %s", exc)

    return entry


def list_entries(
    *,
    bureau: str | None = None,
    timing: Timing | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    store = _load_store()
    entries = list(store.get("entries", []))
    entries.sort(key=lambda e: e.get("created_at", ""), reverse=True)

    if bureau and bureau in VALID_BUREAUS:
        entries = [e for e in entries if e.get("bureau") == bureau]
    if timing in ("now", "later"):
        entries = [e for e in entries if e.get("timing") == timing]

    total = len(entries)
    page = entries[offset : offset + limit]
    counts: dict[str, int] = {b: 0 for b in BUREAU_LABELS}
    timing_counts = {"now": 0, "later": 0}
    for e in store.get("entries", []):
        b = e.get("bureau", "hub")
        if b in counts:
            counts[b] += 1
        t = e.get("timing", "later")
        if t in timing_counts:
            timing_counts[t] += 1

    return {
        "entries": page,
        "total": total,
        "counts_by_bureau": counts,
        "counts_by_timing": timing_counts,
    }


def get_bureaus_meta() -> list[dict[str, Any]]:
    counts = list_entries(limit=0)["counts_by_bureau"]
    return [
        {"id": bid, "label": label, "entry_count": counts.get(bid, 0)}
        for bid, label in BUREAU_LABELS.items()
    ]
