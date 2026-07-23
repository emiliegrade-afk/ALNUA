"""Library retention — compress learned articles, purge stale / low-value entries."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.library_distribution import (
    expected_slots_for_entry,
    receipt_key,
    _load_ledger,
)
from services.bureau_library import (
    _load_store,
    _save_store,
    _utc_now,
)

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
POLICY_FILE = ROOT / "data" / "library_retention_policy.json"

DEFAULT_POLICY = {
    "purge_unused_later_days": 180,
    "compress_when_all_learned": True,
    "purge_empty_summaries": True,
    "purge_duplicate_titles": True,
    "min_summary_chars": 40,
}


def _load_policy() -> dict[str, Any]:
    if not POLICY_FILE.is_file():
        return dict(DEFAULT_POLICY)
    try:
        data = json.loads(POLICY_FILE.read_text(encoding="utf-8"))
        return {**DEFAULT_POLICY, **data}
    except Exception:
        return dict(DEFAULT_POLICY)


def save_policy(updates: dict[str, Any]) -> dict[str, Any]:
    policy = _load_policy()
    policy.update(updates)
    POLICY_FILE.parent.mkdir(parents=True, exist_ok=True)
    POLICY_FILE.write_text(
        json.dumps(policy, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return policy


def _parse_ts(value: str) -> float | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except Exception:
        return None


def _normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip().lower())[:120]


def _entry_fully_learned(entry_id: str, bureau: str, receipts: dict) -> bool:
    agents = expected_slots_for_entry({"bureau": bureau})
    if not agents:
        return False
    for agent_id in agents:
        row = receipts.get(receipt_key(entry_id, agent_id), {})
        if not row.get("learned_at"):
            return False
    return True


def _entry_never_touched(entry_id: str, bureau: str, receipts: dict) -> bool:
    for agent_id in expected_slots_for_entry({"bureau": bureau}):
        row = receipts.get(receipt_key(entry_id, agent_id), {})
        if row.get("distributed_at") or row.get("learned_at"):
            return False
    return True


def preview_retention() -> dict[str, Any]:
    """Dry-run — counts candidates without mutating the library."""
    policy = _load_policy()
    store = _load_store()
    entries: list[dict[str, Any]] = list(store.get("entries", []))
    receipts = _load_ledger().get("receipts", {})
    now = datetime.now(timezone.utc).timestamp()
    purge_days = int(policy.get("purge_unused_later_days", 180))
    min_chars = int(policy.get("min_summary_chars", 40))

    compress_ids: list[str] = []
    purge_ids: list[str] = []
    purge_reasons: dict[str, str] = {}
    seen_titles: dict[str, str] = {}

    for entry in entries:
        eid = str(entry.get("id") or "")
        bureau = str(entry.get("bureau") or "hub")
        title = str(entry.get("title") or "")
        summary = str(entry.get("summary") or "")
        timing = str(entry.get("timing") or "later")
        created = _parse_ts(str(entry.get("created_at") or ""))

        if policy.get("compress_when_all_learned") and _entry_fully_learned(
            eid, bureau, receipts
        ):
            compress_ids.append(eid)
            continue

        norm = _normalize_title(title)
        if policy.get("purge_duplicate_titles") and norm and norm in seen_titles:
            purge_ids.append(eid)
            purge_reasons[eid] = f"Doublon de « {seen_titles[norm][:40]} »"
            continue
        if norm:
            seen_titles.setdefault(norm, title)

        if policy.get("purge_empty_summaries") and len(summary.strip()) < min_chars:
            purge_ids.append(eid)
            purge_reasons[eid] = "Résumé trop court / vide"
            continue

        if (
            timing == "later"
            and created
            and (now - created) > purge_days * 86400
            and _entry_never_touched(eid, bureau, receipts)
        ):
            purge_ids.append(eid)
            purge_reasons[eid] = f"« À garder » non utilisée depuis {purge_days} j"
            continue

    return {
        "policy": policy,
        "total_entries": len(entries),
        "compress_candidates": len(compress_ids),
        "purge_candidates": len(purge_ids),
        "compress_ids": compress_ids[:50],
        "purge_ids": purge_ids[:50],
        "purge_reasons": {k: purge_reasons[k] for k in purge_ids[:20]},
        "archives_count": len(store.get("archives", [])),
        "message": (
            f"{len(compress_ids)} fiche(s) à compresser (apprises par tous les agents), "
            f"{len(purge_ids)} à purger (stale / doublon / vide)."
        ),
    }


def apply_retention(
    *,
    compress: bool = True,
    purge: bool = True,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Compress learned entries into archives; purge stale low-value rows."""
    preview = preview_retention()
    if dry_run:
        return {**preview, "dry_run": True, "applied": False}

    store = _load_store()
    entries: list[dict[str, Any]] = list(store.get("entries", []))
    archives: list[dict[str, Any]] = list(store.get("archives", []))
    receipts = _load_ledger().get("receipts", {})

    compress_set: set[str] = set()
    if compress:
        for entry in entries:
            eid = str(entry.get("id") or "")
            if _entry_fully_learned(
                eid, str(entry.get("bureau") or "hub"), receipts
            ):
                compress_set.add(eid)

    purge_set: set[str] = set()
    if purge:
        policy = _load_policy()
        now = datetime.now(timezone.utc).timestamp()
        purge_days = int(policy.get("purge_unused_later_days", 180))
        min_chars = int(policy.get("min_summary_chars", 40))
        seen_titles: dict[str, str] = {}
        for entry in entries:
            eid = str(entry.get("id") or "")
            if eid in compress_set:
                continue
            bureau = str(entry.get("bureau") or "hub")
            title = str(entry.get("title") or "")
            summary = str(entry.get("summary") or "")
            timing = str(entry.get("timing") or "later")
            created = _parse_ts(str(entry.get("created_at") or ""))
            norm = _normalize_title(title)
            if policy.get("purge_duplicate_titles") and norm and norm in seen_titles:
                purge_set.add(eid)
                continue
            if norm:
                seen_titles.setdefault(norm, title)
            if policy.get("purge_empty_summaries") and len(summary.strip()) < min_chars:
                purge_set.add(eid)
                continue
            if (
                timing == "later"
                and created
                and (now - created) > purge_days * 86400
                and _entry_never_touched(eid, bureau, receipts)
            ):
                purge_set.add(eid)

    kept: list[dict[str, Any]] = []
    compressed = 0
    purged = 0

    for entry in entries:
        eid = str(entry.get("id") or "")
        if eid in purge_set:
            purged += 1
            continue
        if eid in compress_set:
            archives.append(
                {
                    "id": eid,
                    "bureau": entry.get("bureau"),
                    "title": entry.get("title"),
                    "digest": str(entry.get("summary") or "")[:280],
                    "timing": entry.get("timing"),
                    "archived_at": _utc_now(),
                    "reason": "compressed_after_learned",
                }
            )
            compressed += 1
            continue
        kept.append(entry)

    store["entries"] = kept
    store["archives"] = archives[-5000:]
    _save_store(store)

    return {
        "applied": True,
        "compressed": compressed,
        "purged": purged,
        "remaining_entries": len(kept),
        "archives_total": len(store["archives"]),
        "message": (
            f"Garde-fou appliqué — {compressed} compressée(s), {purged} supprimée(s), "
            f"{len(kept)} fiche(s) actives."
        ),
    }
