"""services/manual_costs.py — periodic manual cost entries.

For providers with no usable metering API (hosting: Railway, Vercel, a VPS
bill...). Rather than guess-integrating every possible host, this is a
plain ledger Emilie (or Jules/accounting) fills in once a month, in the
same shape/report style as cost_monitor.py and elevenlabs_monitor.py so
Jules can combine all three into one picture.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_LEDGER_PATH = Path(__file__).parent.parent / "data" / "manual_costs.json"


def _load() -> list[dict[str, Any]]:
    if not _LEDGER_PATH.is_file():
        return []
    try:
        return json.loads(_LEDGER_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("manual_costs load failed: %s", exc)
        return []


def _save(entries: list[dict[str, Any]]) -> None:
    _LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    _LEDGER_PATH.write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")


def record_manual_cost(
    source: str,
    amount_usd: float,
    *,
    period: str | None = None,
    note: str = "",
) -> dict[str, Any]:
    """source: free label, e.g. 'hosting_railway', 'hosting_vercel', 'domain'."""
    entries = _load()
    entry = {
        "id": uuid.uuid4().hex[:12],
        "source": source,
        "amount_usd": round(amount_usd, 2),
        "period": period or datetime.now(timezone.utc).strftime("%Y-%m"),
        "note": note,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }
    entries.append(entry)
    _save(entries)
    return entry


def delete_manual_cost(entry_id: str) -> bool:
    entries = _load()
    kept = [e for e in entries if e.get("id") != entry_id]
    if len(kept) == len(entries):
        return False
    _save(kept)
    return True


def get_manual_costs_report(months: int = 3) -> dict[str, Any]:
    entries = _load()
    cutoff = datetime.now(timezone.utc)
    cutoff_str = f"{cutoff.year}-{cutoff.month:02d}"

    def _within(period: str) -> bool:
        try:
            y, m = (int(x) for x in period.split("-"))
        except (ValueError, AttributeError):
            return True
        idx = y * 12 + m
        cutoff_idx = cutoff.year * 12 + cutoff.month - (months - 1)
        return idx >= cutoff_idx

    recent = [e for e in entries if _within(e.get("period", ""))]
    by_source: dict[str, float] = {}
    by_period: dict[str, float] = {}
    for e in recent:
        by_source[e["source"]] = round(by_source.get(e["source"], 0.0) + e["amount_usd"], 2)
        by_period[e["period"]] = round(by_period.get(e["period"], 0.0) + e["amount_usd"], 2)

    return {
        "entries": recent,
        "total_usd": round(sum(e["amount_usd"] for e in recent), 2),
        "by_source": by_source,
        "by_period": dict(sorted(by_period.items())),
        "current_period": cutoff_str,
    }
