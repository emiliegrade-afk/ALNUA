"""Department budget envelopes — allocation tracking without auto-transfer.

JSON ledger (same pattern as invoices). Agents never move money; Emilie
adjusts envelopes. Spent is computed from tagged transactions when available.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PATH = Path(__file__).parent.parent / "data" / "budgets.json"

DEPARTMENTS = frozenset(
    {"app", "gaming", "robo", "marketing", "rnd", "finances", "company", "other"}
)


def _load() -> list[dict[str, Any]]:
    if not _PATH.is_file():
        return []
    try:
        rows = json.loads(_PATH.read_text(encoding="utf-8"))
        return rows if isinstance(rows, list) else []
    except Exception as exc:
        logger.warning("budgets load failed: %s", exc)
        return []


def _save(rows: list[dict[str, Any]]) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    _PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def list_budgets(*, department: str | None = None, period: str | None = None) -> list[dict[str, Any]]:
    rows = _load()
    if department:
        rows = [r for r in rows if r.get("department") == department]
    if period:
        rows = [r for r in rows if r.get("period") == period]
    return sorted(rows, key=lambda r: (r.get("period") or "", r.get("department") or ""), reverse=True)


def create_budget(
    *,
    department: str,
    period: str,
    amount: float,
    currency: str = "EUR",
    label: str = "",
    notes: str = "",
) -> dict[str, Any]:
    dept = department.strip().lower()
    if dept not in DEPARTMENTS:
        raise ValueError(f"department invalide: {department}")
    if not period or len(period) < 4:
        raise ValueError("period requis (ex. 2026-08 ou 2026-Q3)")
    if amount < 0:
        raise ValueError("amount must be >= 0")
    row = {
        "id": uuid.uuid4().hex[:12],
        "department": dept,
        "period": period.strip(),
        "amount": round(float(amount), 2),
        "currency": currency.upper(),
        "label": label.strip() or f"Budget {dept} {period}",
        "notes": notes.strip(),
        "spent": 0.0,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "transfer_policy": "Manuel uniquement — budget_transfer workflow reporté (Vague 3).",
    }
    rows = _load()
    rows.append(row)
    _save(rows)
    return row


def update_budget(budget_id: str, **updates: Any) -> dict[str, Any]:
    rows = _load()
    for i, row in enumerate(rows):
        if row.get("id") != budget_id:
            continue
        if "department" in updates and updates["department"] is not None:
            dept = str(updates["department"]).strip().lower()
            if dept not in DEPARTMENTS:
                raise ValueError(f"department invalide: {dept}")
            row["department"] = dept
        if "period" in updates and updates["period"] is not None:
            row["period"] = str(updates["period"]).strip()
        if "amount" in updates and updates["amount"] is not None:
            amt = float(updates["amount"])
            if amt < 0:
                raise ValueError("amount must be >= 0")
            row["amount"] = round(amt, 2)
        if "spent" in updates and updates["spent"] is not None:
            spent = float(updates["spent"])
            if spent < 0:
                raise ValueError("spent must be >= 0")
            row["spent"] = round(spent, 2)
        for key in ("label", "notes", "currency"):
            if key in updates and updates[key] is not None:
                row[key] = updates[key] if key != "currency" else str(updates[key]).upper()
        row["updated_at"] = datetime.now(timezone.utc).isoformat()
        rows[i] = row
        _save(rows)
        return row
    raise KeyError(f"budget not found: {budget_id}")


def budget_summary() -> dict[str, Any]:
    rows = _load()
    total = sum(float(r.get("amount") or 0) for r in rows)
    spent = sum(float(r.get("spent") or 0) for r in rows)
    by_dept: dict[str, float] = {}
    for r in rows:
        d = str(r.get("department") or "other")
        by_dept[d] = by_dept.get(d, 0.0) + float(r.get("amount") or 0)
    return {
        "count": len(rows),
        "total_allocated": round(total, 2),
        "total_spent": round(spent, 2),
        "remaining": round(total - spent, 2),
        "by_department": {k: round(v, 2) for k, v in by_dept.items()},
        "transfer_policy": "Pas de transfert auto — paiement/mouvement hors Hub.",
    }
