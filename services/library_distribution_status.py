"""Library distribution — CEO dashboard status aggregation."""

from __future__ import annotations

import json
import logging
import time
from typing import Any

from services.library_distribution_store import (
    _active_job_snapshot,
    _load_ledger,
    receipt_key,
)
from services.team_enrichment import BUREAU_AGENTS, agents_for_bureau

logger = logging.getLogger(__name__)

_STATUS_CACHE: dict[str, Any] | None = None
_STATUS_CACHE_AT: float = 0.0
_STATUS_CACHE_TTL = 25.0


def invalidate_status_cache() -> None:
    global _STATUS_CACHE
    _STATUS_CACHE = None


def _load_all_entries() -> list[dict[str, Any]]:
    from services.bureau_library import LIBRARY_FILE

    if not LIBRARY_FILE.is_file():
        return []
    try:
        store = json.loads(LIBRARY_FILE.read_text(encoding="utf-8"))
        return list(store.get("entries", []))
    except Exception:
        return []


def expected_slots_for_entry(entry: dict[str, Any]) -> list[str]:
    return agents_for_bureau(str(entry.get("bureau") or "hub"))


def get_distribution_status(*, force: bool = False) -> dict[str, Any]:
    """CEO dashboard — cached to avoid blocking API on 4k+ entries."""
    global _STATUS_CACHE, _STATUS_CACHE_AT
    now = time.monotonic()
    if (
        not force
        and _STATUS_CACHE
        and (now - _STATUS_CACHE_AT) < _STATUS_CACHE_TTL
    ):
        cached = dict(_STATUS_CACHE)
        cached["active_job"] = _active_job_snapshot(_load_ledger())
        cached["cached"] = True
        return cached

    entries = _load_all_entries()
    ledger = _load_ledger()
    receipts: dict[str, dict[str, Any]] = ledger.get("receipts", {})

    total_entries = len(entries)
    total_slots = 0
    distributed_slots = 0
    learned_slots = 0
    verified_slots = 0
    mem0_confirmed = 0
    entries_fully_distributed = 0
    entries_fully_learned = 0
    entries_fully_verified = 0
    by_bureau: dict[str, dict[str, int]] = {}

    for entry in entries:
        entry_id = str(entry.get("id") or "")
        bureau = str(entry.get("bureau") or "hub")
        agents = expected_slots_for_entry(entry)
        bureau_stats = by_bureau.setdefault(
            bureau,
            {
                "entries": 0,
                "slots": 0,
                "distributed": 0,
                "learned": 0,
                "verified": 0,
            },
        )
        bureau_stats["entries"] += 1

        all_dist = True
        all_learned = True
        all_verified = True

        for agent_id in agents:
            total_slots += 1
            bureau_stats["slots"] += 1
            row = receipts.get(receipt_key(entry_id, agent_id), {})

            if row.get("distributed_at"):
                distributed_slots += 1
                bureau_stats["distributed"] += 1
            else:
                all_dist = False

            if row.get("learned_at"):
                learned_slots += 1
                bureau_stats["learned"] += 1
            else:
                all_learned = False

            if row.get("verified_at"):
                verified_slots += 1
                bureau_stats["verified"] += 1
                if row.get("mem0_found"):
                    mem0_confirmed += 1
                else:
                    all_verified = False
            else:
                all_verified = False

        if all_dist and agents:
            entries_fully_distributed += 1
        if all_learned and agents:
            entries_fully_learned += 1
        if all_verified and agents:
            entries_fully_verified += 1

    active_job = _active_job_snapshot(ledger)

    from services.bureau_library import list_entries

    lib_meta = list_entries(limit=0)
    now_count = lib_meta.get("counts_by_timing", {}).get("now", 0)

    def pct(num: int, den: int) -> float:
        return round((num / den * 100) if den else 0.0, 1)

    result = {
        "total_entries": total_entries,
        "library_entries": total_entries,
        "library_now": now_count,
        "total_slots": total_slots,
        "distributed_slots": distributed_slots,
        "learned_slots": learned_slots,
        "verified_slots": verified_slots,
        "mem0_confirmed_slots": mem0_confirmed,
        "entries_fully_distributed": entries_fully_distributed,
        "entries_fully_learned": entries_fully_learned,
        "entries_fully_verified": entries_fully_verified,
        "entries_pending_distribution": total_entries - entries_fully_distributed,
        "distribution_pct": pct(distributed_slots, total_slots),
        "learned_pct": pct(learned_slots, total_slots),
        "verified_pct": pct(mem0_confirmed, total_slots),
        "agents_total": sum(len(v) for v in BUREAU_AGENTS.values()),
        "agents_with_memories": learned_slots,
        "bureaus": len(BUREAU_AGENTS),
        "by_bureau": by_bureau,
        "active_job": active_job,
        "ledger_receipts": len(receipts),
        "cached": False,
    }
    _STATUS_CACHE = result
    _STATUS_CACHE_AT = now
    return result
