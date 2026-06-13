"""BOM Eve — CRUD helpers (service role via Supabase client)."""

from __future__ import annotations

from typing import Any

from database.supabase_client import SupabaseClient, get_supabase

BOM_CATEGORIES = (
    "vision",
    "audio",
    "moteur",
    "alimentation",
    "microcontroleur",
    "chassis",
    "compute",
    "autre",
)

BOM_STATUSES = ("a_commander", "commande", "livre", "utilise")


def list_bom_items(db: SupabaseClient | None = None) -> list[dict[str, Any]]:
    sb = db or get_supabase()
    return sb.select("bom_eve", order_by="created_at", ascending=False)


def create_bom_item(data: dict[str, Any], db: SupabaseClient | None = None) -> dict[str, Any]:
    sb = db or get_supabase()
    category = data.get("category", "autre")
    if category not in BOM_CATEGORIES:
        raise ValueError(f"Invalid category: {category}")
    status = data.get("status", "a_commander")
    if status not in BOM_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    row = {
        "component": data["component"],
        "category": category,
        "quantity": int(data.get("quantity", 1)),
        "unit_price": data.get("unit_price"),
        "supplier": data.get("supplier"),
        "url": data.get("url"),
        "status": status,
        "notes": data.get("notes"),
        "project_slug": data.get("project_slug", "eve"),
    }
    return sb.insert("bom_eve", row)


def update_bom_item(
    item_id: str,
    data: dict[str, Any],
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    sb = db or get_supabase()
    updates: dict[str, Any] = {}
    for key in (
        "component",
        "category",
        "quantity",
        "unit_price",
        "supplier",
        "url",
        "status",
        "notes",
        "project_slug",
    ):
        if key in data and data[key] is not None:
            updates[key] = data[key]
    if "category" in updates and updates["category"] not in BOM_CATEGORIES:
        raise ValueError(f"Invalid category: {updates['category']}")
    if "status" in updates and updates["status"] not in BOM_STATUSES:
        raise ValueError(f"Invalid status: {updates['status']}")
    return sb.update("bom_eve", item_id, updates)


def delete_bom_item(item_id: str, db: SupabaseClient | None = None) -> dict[str, Any]:
    sb = db or get_supabase()
    sb.delete("bom_eve", item_id)
    return {"ok": True, "id": item_id}


def bom_totals(items: list[dict[str, Any]]) -> dict[str, Any]:
    total = 0.0
    by_category: dict[str, float] = {}
    for row in items:
        qty = int(row.get("quantity") or 1)
        price = float(row.get("unit_price") or row.get("total_price") or 0)
        line = qty * price
        total += line
        cat = str(row.get("category") or "autre")
        by_category[cat] = by_category.get(cat, 0.0) + line
    return {"total_eur": round(total, 2), "by_category": by_category, "count": len(items)}
