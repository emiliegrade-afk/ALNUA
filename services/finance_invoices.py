"""Invoice ledger for Jules — manage invoices without executing payment.

Payment is always external (Emilie via Revolut / bank). Agents can:
create, list, update status (draft→received→to_pay→paid_externally).
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_PATH = Path(__file__).parent.parent / "data" / "invoices.json"

VALID_STATUSES = frozenset(
    {"draft", "received", "to_pay", "paid_externally", "cancelled"}
)


def _load() -> list[dict[str, Any]]:
    if not _PATH.is_file():
        return []
    try:
        return json.loads(_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.warning("invoices load failed: %s", exc)
        return []


def _save(rows: list[dict[str, Any]]) -> None:
    _PATH.parent.mkdir(parents=True, exist_ok=True)
    _PATH.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")


def list_invoices(
    *,
    status: str | None = None,
    vendor: str | None = None,
) -> list[dict[str, Any]]:
    rows = _load()
    if status:
        rows = [r for r in rows if r.get("status") == status]
    if vendor:
        v = vendor.lower()
        rows = [r for r in rows if v in str(r.get("vendor", "")).lower()]
    if status == "to_pay":
        return sorted(rows, key=lambda r: r.get("due_date") or "9999-12-31")
    return sorted(rows, key=lambda r: r.get("due_date") or r.get("created_at") or "", reverse=True)


def create_invoice(
    *,
    vendor: str,
    amount: float,
    currency: str = "EUR",
    description: str = "",
    due_date: str | None = None,
    category: str = "saas_tools",
    receipt_url: str = "",
    external_ref: str = "",
    status: str = "received",
) -> dict[str, Any]:
    if status not in VALID_STATUSES:
        raise ValueError(f"status invalide: {status}")
    if amount <= 0:
        raise ValueError("amount must be > 0")
    row = {
        "id": uuid.uuid4().hex[:12],
        "vendor": vendor.strip(),
        "amount": round(float(amount), 2),
        "currency": currency.upper(),
        "description": description.strip(),
        "due_date": due_date or date.today().isoformat(),
        "category": category,
        "receipt_url": receipt_url,
        "external_ref": external_ref,
        "status": status,
        "paid_at": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "notes": "Paiement externe uniquement (Revolut/Emilie) — agents ne paient pas.",
    }
    rows = _load()
    rows.append(row)
    _save(rows)
    return row


def update_invoice(invoice_id: str, **updates: Any) -> dict[str, Any]:
    rows = _load()
    for i, row in enumerate(rows):
        if row.get("id") != invoice_id:
            continue
        if "status" in updates and updates["status"] is not None:
            if updates["status"] not in VALID_STATUSES:
                raise ValueError(f"status invalide: {updates['status']}")
            row["status"] = updates["status"]
            if updates["status"] == "paid_externally":
                row["paid_at"] = datetime.now(timezone.utc).isoformat()
        for key in ("vendor", "description", "due_date", "category", "receipt_url", "external_ref", "notes"):
            if key in updates and updates[key] is not None:
                row[key] = updates[key]
        if "amount" in updates and updates["amount"] is not None:
            amt = float(updates["amount"])
            if amt <= 0:
                raise ValueError("amount must be > 0")
            row["amount"] = round(amt, 2)
        row["updated_at"] = datetime.now(timezone.utc).isoformat()
        rows[i] = row
        _save(rows)
        return row
    raise KeyError(f"invoice not found: {invoice_id}")


def invoice_summary() -> dict[str, Any]:
    rows = _load()
    by_status: dict[str, float] = {}
    for r in rows:
        st = r.get("status", "draft")
        by_status[st] = round(by_status.get(st, 0.0) + float(r.get("amount") or 0), 2)
    to_pay = [r for r in rows if r.get("status") == "to_pay"]
    return {
        "count": len(rows),
        "by_status_amount": by_status,
        "to_pay_count": len(to_pay),
        "to_pay_total": round(sum(float(r.get("amount") or 0) for r in to_pay), 2),
        "payment_policy": "Agents gèrent le suivi ; Emilie paie via Revolut/banque.",
    }
