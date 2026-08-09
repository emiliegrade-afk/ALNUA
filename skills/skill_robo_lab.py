"""Eve lab / builds context for Phase 21 robotics agents (Vague B).

Honest empty — never invents pass/fail telemetry when Supabase is down or empty.
"""
from __future__ import annotations

from typing import Any


def get_lab_context(
    *,
    project_id: str | None = None,
    category: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Snapshot of robo_lab_tests for QA / Safety / Simulation grounding."""
    try:
        from database.supabase_client import get_supabase

        db = get_supabase()
        filters: dict[str, Any] = {}
        if project_id:
            filters["project_id"] = project_id
        if category:
            filters["category"] = category
        rows = db.select(
            "robo_lab_tests",
            filters=filters or None,
            order_by="created_at",
            ascending=False,
            limit=max(1, min(limit, 100)),
        )
    except Exception as exc:
        return {
            "ok": False,
            "error": f"Lab tests indisponibles: {exc}",
            "items": [],
            "count": 0,
        }

    slim = [
        {
            "id": r.get("id"),
            "project_id": r.get("project_id"),
            "category": r.get("category"),
            "name": r.get("name"),
            "status": r.get("status"),
            "measured_value": r.get("measured_value"),
            "notes": (r.get("notes") or "")[:200],
            "created_at": r.get("created_at"),
        }
        for r in (rows or [])
    ]
    return {
        "ok": True,
        "count": len(slim),
        "items": slim,
        "empty": len(slim) == 0,
        "message": None if slim else "Aucun banc de test enregistré — receptacle Phase 19 vide.",
    }


def get_builds_context(
    *,
    project_id: str | None = None,
    limit: int = 10,
) -> dict[str, Any]:
    """Snapshot of robo_builds for Safety / Simulation grounding."""
    try:
        from database.supabase_client import get_supabase

        db = get_supabase()
        filters: dict[str, Any] = {}
        if project_id:
            filters["project_id"] = project_id
        rows = db.select(
            "robo_builds",
            filters=filters or None,
            order_by="created_at",
            ascending=False,
            limit=max(1, min(limit, 50)),
        )
    except Exception as exc:
        return {
            "ok": False,
            "error": f"Builds robotique indisponibles: {exc}",
            "items": [],
            "count": 0,
        }

    slim = [
        {
            "id": r.get("id"),
            "project_id": r.get("project_id"),
            "branch": r.get("branch"),
            "stage": r.get("stage"),
            "version": r.get("version"),
            "pcb_revision": r.get("pcb_revision"),
            "firmware_version": r.get("firmware_version"),
            "tests_passed_pct": r.get("tests_passed_pct"),
            "open_issues": r.get("open_issues"),
            "notes": (r.get("notes") or "")[:200],
        }
        for r in (rows or [])
    ]
    return {
        "ok": True,
        "count": len(slim),
        "items": slim,
        "empty": len(slim) == 0,
        "message": None if slim else "Aucun build robotique enregistré.",
    }


def get_lab_bundle(
    *,
    project_id: str | None = None,
    category: str | None = None,
) -> dict[str, Any]:
    """Lab + builds in one payload for Safety / Simulation."""
    lab = get_lab_context(project_id=project_id, category=category)
    builds = get_builds_context(project_id=project_id)
    ok = bool(lab.get("ok")) and bool(builds.get("ok"))
    return {
        "ok": ok,
        "lab": lab,
        "builds": builds,
        "error": None if ok else (lab.get("error") or builds.get("error")),
    }
