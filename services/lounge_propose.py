"""
Lounge → enterprise propose (DEC-031 / Phase 46 V5).

Creates a Hub ticket for human validation — never writes prod directly.
"""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config.agent_models import normalize_agent_id
from services.input_sanitizer import sanitize_user_input
from services.lounge_runtime import get_session

_PROPOSALS_PATH = Path(__file__).resolve().parent.parent / "data" / "lounge_proposals.json"
_lock = threading.Lock()

DEPT_LABELS = {
    "app": "APP",
    "rd": "R&D",
    "gaming": "Gaming",
    "robo": "Robotique",
    "marketing": "Marketing",
    "hub": "Direction / Hub",
    "finances": "Finance",
    "analytics": "Analytics",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _load() -> dict[str, Any]:
    if not _PROPOSALS_PATH.exists():
        return {"proposals": [], "updated_at": _now()}
    data = json.loads(_PROPOSALS_PATH.read_text(encoding="utf-8"))
    data.setdefault("proposals", [])
    return data


def _save(data: dict[str, Any]) -> None:
    data["updated_at"] = _now()
    _PROPOSALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    props = data.get("proposals", [])
    if len(props) > 300:
        data["proposals"] = props[-300:]
    _PROPOSALS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def _resolve_project_id(project_id: str | None) -> str | None:
    if project_id and project_id.strip():
        return project_id.strip()
    try:
        from database.supabase_client import get_supabase

        projects = get_supabase().select("projects", limit=1) or []
        if projects:
            return str(projects[0].get("id") or "") or None
    except Exception:
        return None
    return None


def propose_to_department(
    *,
    session_id: str,
    dept: str,
    summary: str,
    project_id: str | None = None,
    agent_id: str | None = None,
) -> dict[str, Any]:
    """Turn a Lounge session insight into a Hub ticket (validation required)."""
    dept_key = (dept or "hub").strip().lower()
    if dept_key not in DEPT_LABELS:
        raise ValueError(f"unknown dept: {dept_key}")

    clean_summary = sanitize_user_input(
        summary or "",
        max_length=2000,
        redact_pii_enabled=False,
    )
    if len(clean_summary) < 8:
        raise ValueError("summary too short")

    session = get_session(session_id)
    if session is None:
        raise KeyError(f"session not found: {session_id}")

    aid = normalize_agent_id(agent_id or str(session.get("agent_id") or "coo"))
    title_bit = sanitize_user_input(
        str(session.get("puzzle_title") or session.get("activity") or "insight"),
        max_length=80,
        redact_pii_enabled=False,
    )
    title = f"[lounge] {DEPT_LABELS[dept_key]} — {title_bit}"[:120]

    description = (
        f"Proposition depuis Agent Lounge (validation requise — pas d'auto-apply).\n\n"
        f"Département cible : {DEPT_LABELS[dept_key]}\n"
        f"Agent : {aid}\n"
        f"Session : {session_id}\n"
        f"Activité : {session.get('activity')}\n"
        f"Puzzle : {session.get('puzzle_title')} ({session.get('puzzle_id')})\n"
        f"Résultat session : won={session.get('won')} · "
        f"réponse={session.get('agent_answer')}\n\n"
        f"Résumé / idée :\n{clean_summary}\n"
    )

    pid = _resolve_project_id(project_id)
    ticket: dict[str, Any] | None = None
    ticket_error: str | None = None

    if pid:
        try:
            from database.supabase_client import get_supabase

            ticket = get_supabase().insert(
                "tickets",
                {
                    "project_id": pid,
                    "type": "improvement",
                    "priority": "medium",
                    "title": title,
                    "description": description,
                    "source": "lounge",
                    "status": "open",
                    "assignee_agent_id": aid,
                    "story_points": None,
                    "due_date": None,
                },
            )
        except Exception as exc:
            ticket_error = str(exc)[:300]
    else:
        ticket_error = "no_project_id"

    proposal = {
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "agent_id": aid,
        "dept": dept_key,
        "summary": clean_summary,
        "title": title,
        "project_id": pid,
        "ticket_id": (ticket or {}).get("id") if isinstance(ticket, dict) else None,
        "ticket_error": ticket_error,
        "status": "ticket_created" if ticket else "logged_only",
        "created_at": _now(),
    }

    with _lock:
        data = _load()
        data["proposals"].append(proposal)
        _save(data)

    return {
        "ok": bool(ticket),
        "proposal": proposal,
        "ticket": ticket,
        "message": (
            "Ticket créé — validation humaine requise avant prod."
            if ticket
            else f"Proposition journalisée ({ticket_error}) — pas de ticket."
        ),
    }


def list_proposals(*, limit: int = 30) -> list[dict[str, Any]]:
    with _lock:
        data = _load()
        props = list(reversed(data.get("proposals") or []))
    return props[: max(1, min(limit, 100))]


def contributions_transferred_count() -> int:
    with _lock:
        data = _load()
        return sum(
            1
            for p in data.get("proposals") or []
            if p.get("status") == "ticket_created"
        )
