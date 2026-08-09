"""Fiscal obligations ledger — due dates and external payment status.

No auto-declaration, no auto-pay. Status paid_externally only after Emilie pays.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PATH = Path(__file__).parent.parent / "data" / "fiscal_obligations.json"

VALID_STATUSES = frozenset({"upcoming", "due", "paid_externally", "cancelled"})
KINDS = frozenset(
    {"tva", "urssaf", "impot", "cfe", "retraite", "assurance", "autre"}
)


def _load() -> list[dict[str, Any]]:
    if not _PATH.is_file():
        return []
    try:
        rows = json.loads(_PATH.read_text(encoding="utf-8"))
        return rows if isinstance(rows, list) else []
    except Exception as exc:
        logger.warning("fiscal_obligations load failed: %s", exc)
        return []


def _save(rows: list[dict[str, Any]]) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    _PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def list_obligations(
    *,
    status: str | None = None,
    kind: str | None = None,
) -> list[dict[str, Any]]:
    rows = _load()
    if status:
        rows = [r for r in rows if r.get("status") == status]
    if kind:
        rows = [r for r in rows if r.get("kind") == kind]
    return sorted(rows, key=lambda r: r.get("due_date") or "", reverse=False)


def create_obligation(
    *,
    title: str,
    amount: float,
    due_date: str | None = None,
    kind: str = "autre",
    currency: str = "EUR",
    notes: str = "",
    status: str = "upcoming",
) -> dict[str, Any]:
    k = kind.strip().lower()
    if k not in KINDS:
        raise ValueError(f"kind invalide: {kind}")
    if status not in VALID_STATUSES:
        raise ValueError(f"status invalide: {status}")
    if amount < 0:
        raise ValueError("amount must be >= 0")
    title_clean = title.strip()
    if not title_clean:
        raise ValueError("title requis")
    row = {
        "id": uuid.uuid4().hex[:12],
        "title": title_clean,
        "kind": k,
        "amount": round(float(amount), 2),
        "currency": currency.upper(),
        "due_date": due_date or date.today().isoformat(),
        "status": status,
        "notes": notes.strip(),
        "paid_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "payment_policy": "Paiement externe uniquement — agents ne paient pas.",
    }
    rows = _load()
    rows.append(row)
    _save(rows)
    return row


def update_obligation(obligation_id: str, **updates: Any) -> dict[str, Any]:
    rows = _load()
    for i, row in enumerate(rows):
        if row.get("id") != obligation_id:
            continue
        if "status" in updates and updates["status"] is not None:
            if updates["status"] not in VALID_STATUSES:
                raise ValueError(f"status invalide: {updates['status']}")
            row["status"] = updates["status"]
            if updates["status"] == "paid_externally":
                row["paid_at"] = datetime.now(timezone.utc).isoformat()
        if "kind" in updates and updates["kind"] is not None:
            k = str(updates["kind"]).strip().lower()
            if k not in KINDS:
                raise ValueError(f"kind invalide: {k}")
            row["kind"] = k
        if "amount" in updates and updates["amount"] is not None:
            amt = float(updates["amount"])
            if amt < 0:
                raise ValueError("amount must be >= 0")
            row["amount"] = round(amt, 2)
        for key in ("title", "due_date", "notes", "currency"):
            if key in updates and updates[key] is not None:
                row[key] = updates[key] if key != "currency" else str(updates[key]).upper()
        row["updated_at"] = datetime.now(timezone.utc).isoformat()
        rows[i] = row
        _save(rows)
        return row
    raise KeyError(f"obligation not found: {obligation_id}")


def fiscal_summary() -> dict[str, Any]:
    rows = _load()
    open_rows = [r for r in rows if r.get("status") in ("upcoming", "due")]
    open_total = sum(float(r.get("amount") or 0) for r in open_rows)
    return {
        "count": len(rows),
        "open_count": len(open_rows),
        "open_total": round(open_total, 2),
        "next_due": open_rows[0]["due_date"] if open_rows else None,
        "payment_policy": "Paiement externe uniquement (banque / impôts.gouv).",
    }
