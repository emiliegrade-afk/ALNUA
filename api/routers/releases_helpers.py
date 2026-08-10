"""Shared helpers for releases router."""

from __future__ import annotations

from typing import Any

from services.input_sanitizer import sanitize_user_input


def clean_release_text(text: str, *, max_length: int = 6000) -> str:
    return sanitize_user_input(text, max_length=max_length)


def enrich_releases_with_project_names(
    db: Any, releases: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not releases:
        return releases
    project_ids = {r["project_id"] for r in releases if r.get("project_id")}
    names: dict[str, str] = {}
    for pid in project_ids:
        rows = db.select("projects", filters={"id": pid}, columns="id,name")
        if rows:
            names[pid] = rows[0]["name"]
    for release in releases:
        pid = release.get("project_id")
        if pid and pid in names:
            release["project_name"] = names[pid]
    return releases
