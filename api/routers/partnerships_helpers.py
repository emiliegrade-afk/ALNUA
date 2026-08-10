"""Shared helpers for partnerships routers."""

from __future__ import annotations

from typing import Any


def partner_row_to_api(row: dict[str, Any]) -> dict[str, Any]:
    return {
        **row,
        "project_ids": row.get("project_ids") or [],
    }


def serialize_partner_dates(values: dict[str, Any]) -> dict[str, Any]:
    out = dict(values)
    for key in ("next_followup", "last_contact_date"):
        if key in out and out[key] is not None and hasattr(out[key], "isoformat"):
            out[key] = out[key].isoformat()
    return out
