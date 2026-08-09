"""Revolut Business — read-only expenses for ALNUA accounting.

Requires Grow+ Business API access token in .env:
  REVOLUT_ACCESS_TOKEN=...
  REVOLUT_API_BASE=https://b2b.revolut.com/api/1.0   (default)

Does NOT initiate payments — Jules/Rémi read & categorize only.
Payment stays manual in the Revolut app (Emilie).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from config.settings import get_settings

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    return bool(get_settings().revolut_access_token.strip())


def _headers() -> dict[str, str]:
    token = get_settings().revolut_access_token.strip()
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json",
    }


def fetch_expenses_summary(*, days: int = 30, count: int = 100) -> dict[str, Any]:
    """GET /expenses — returns total EUR + slim rows for the cockpit."""
    settings = get_settings()
    token = settings.revolut_access_token.strip()
    if not token:
        return {
            "configured": False,
            "reason": (
                "REVOLUT_ACCESS_TOKEN manquant. "
                "Revolut Business → Settings → APIs (plan Grow+) → créer un accès, "
                "puis coller le token dans .env. Lecture seule — aucun paiement auto."
            ),
            "expenses": [],
            "total_eur": 0.0,
        }

    base = (settings.revolut_api_base or "https://b2b.revolut.com/api/1.0").rstrip("/")
    since = datetime.now(timezone.utc) - timedelta(days=max(1, days))
    params = {
        "from": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "count": min(max(1, count), 500),
    }
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.get(f"{base}/expenses", headers=_headers(), params=params)
        if resp.status_code >= 400:
            return {
                "configured": True,
                "ok": False,
                "error": f"Revolut HTTP {resp.status_code}: {resp.text[:300]}",
                "expenses": [],
                "total_eur": 0.0,
            }
        raw = resp.json()
    except Exception as exc:
        logger.warning("revolut expenses failed: %s", exc)
        return {
            "configured": True,
            "ok": False,
            "error": str(exc)[:300],
            "expenses": [],
            "total_eur": 0.0,
        }

    rows = raw if isinstance(raw, list) else raw.get("expenses") or raw.get("items") or []
    slim: list[dict[str, Any]] = []
    total = 0.0
    for e in rows:
        if not isinstance(e, dict):
            continue
        # Revolut amounts are often minor units (cents) under amount / transaction_amount
        amount_obj = e.get("transaction_amount") or e.get("amount") or {}
        currency = "EUR"
        major = 0.0
        if isinstance(amount_obj, dict):
            value = amount_obj.get("value") or amount_obj.get("amount") or 0
            currency = str(amount_obj.get("currency") or "EUR")
            try:
                # Revolut Business usually returns minor units as int
                raw_v = float(value)
                major = raw_v / 100.0 if abs(raw_v) >= 1 and float(value) == int(float(value)) else raw_v
                if isinstance(value, str) and "." in value:
                    major = float(value)
            except (TypeError, ValueError):
                major = 0.0
        else:
            try:
                major = float(amount_obj or 0)
            except (TypeError, ValueError):
                major = 0.0
        total += major
        slim.append(
            {
                "id": e.get("id"),
                "state": e.get("state"),
                "description": e.get("description") or e.get("merchant", {}).get("name")
                if isinstance(e.get("merchant"), dict)
                else e.get("description"),
                "amount": round(major, 2),
                "currency": currency,
                "expense_date": e.get("expense_date") or e.get("created_at"),
            }
        )

    return {
        "configured": True,
        "ok": True,
        "expenses": slim,
        "total_eur": round(total, 2),
        "count": len(slim),
        "days": days,
    }
