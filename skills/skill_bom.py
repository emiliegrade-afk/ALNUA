"""Thin BOM skill wrapping services.eve_bom — shared by electronics / mechanical."""

from __future__ import annotations

from typing import Any

from services.eve_bom import BOM_CATEGORIES, BOM_STATUSES, list_bom_items


def bom_is_available() -> bool:
    """True if Supabase BOM table is reachable (empty list still counts as available)."""
    try:
        list_bom_items()
        return True
    except Exception:
        return False


def get_bom_context(
    *,
    category: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Return a compact BOM snapshot for agent prompts / UI.

    Never fabricates lines. On DB failure returns explicit error.
    """
    try:
        items = list_bom_items()
    except Exception as exc:
        return {
            "ok": False,
            "error": f"BOM indisponible: {exc}",
            "items": [],
            "categories": list(BOM_CATEGORIES),
            "statuses": list(BOM_STATUSES),
        }

    if category:
        cat = category.strip().lower()
        items = [i for i in items if str(i.get("category", "")).lower() == cat]

    slim = []
    for row in items[: max(1, min(limit, 100))]:
        slim.append(
            {
                "id": row.get("id"),
                "component": row.get("component"),
                "category": row.get("category"),
                "quantity": row.get("quantity"),
                "status": row.get("status"),
                "unit_price": row.get("unit_price"),
                "supplier": row.get("supplier"),
            }
        )
    return {
        "ok": True,
        "count": len(items),
        "items": slim,
        "categories": list(BOM_CATEGORIES),
        "statuses": list(BOM_STATUSES),
    }
