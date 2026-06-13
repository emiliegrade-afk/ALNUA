"""Committee sessions and messages for R&D dossiers (phase 3)."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime
from typing import Any

from database.supabase_client import SupabaseClient, get_supabase

logger = logging.getLogger(__name__)

COMMITTEE_MEMBERS: dict[str, dict[str, str]] = {
    "pm": {"id": "pm", "name": "Alex", "title": "Chef de projet", "emoji": "📋", "agent_id": "pm"},
    "spec": {"id": "spec", "name": "Spec", "title": "Spécifications", "emoji": "📐", "agent_id": "spec"},
    "marketing": {"id": "marketing", "name": "Maya", "title": "Marketing", "emoji": "📣", "agent_id": "marketing"},
    "accounting": {"id": "accounting", "name": "Compta", "title": "Finance", "emoji": "💰", "agent_id": "accounting"},
    "dev_app": {"id": "dev_app", "name": "Dev App", "title": "Dev mobile/web", "emoji": "📱", "agent_id": "dev_app"},
    "dev_gaming": {"id": "dev_gaming", "name": "Dev Gaming", "title": "Dev jeu", "emoji": "🎮", "agent_id": "dev_gaming"},
    "game_director": {"id": "game_director", "name": "Game Dir.", "title": "Direction jeu", "emoji": "🎯", "agent_id": "game_director"},
    "hardware": {"id": "hardware", "name": "Hardware", "title": "Hardware", "emoji": "🔧", "agent_id": "hardware"},
    "embedded_dev": {"id": "embedded_dev", "name": "Embedded", "title": "Firmware", "emoji": "⚡", "agent_id": "embedded_dev"},
    "content": {"id": "content", "name": "Content", "title": "Contenu & social", "emoji": "✍️", "agent_id": "content"},
}

DOMAIN_EXTRA_MEMBERS: dict[str, list[str]] = {
    "saas": ["dev_app"],
    "app": ["dev_app"],
    "ia": ["dev_app"],
    "jeu": ["game_director", "dev_gaming"],
    "game": ["game_director", "dev_gaming"],
    "gaming": ["game_director", "dev_gaming"],
    "hardware": ["hardware", "embedded_dev"],
    "robotique": ["hardware", "embedded_dev"],
    "robotics": ["hardware", "embedded_dev"],
}

CORE_MEMBERS = ["pm", "spec", "marketing", "accounting"]


def build_committee_team(domain: str | None) -> list[dict[str, str]]:
    dom = (domain or "autre").lower()
    ids = list(CORE_MEMBERS)
    for extra in DOMAIN_EXTRA_MEMBERS.get(dom, ["dev_app"] if dom in ("autre",) else []):
        if extra not in ids:
            ids.append(extra)
    if "content" not in ids:
        ids.append("content")
    return [dict(COMMITTEE_MEMBERS[mid]) for mid in ids if mid in COMMITTEE_MEMBERS]


def member_label(member_id: str) -> str:
    m = COMMITTEE_MEMBERS.get(member_id, {})
    return f"{m.get('emoji', '🤖')} {m.get('name', member_id)}"


class RndCommitteeRepository:
    def __init__(self, db: SupabaseClient | None = None) -> None:
        self.db = db or get_supabase()

    def create_session(
        self,
        dossier_id: str,
        *,
        title: str,
        team: list[dict[str, Any]],
        mode: str = "free",
        active_section: str | None = None,
    ) -> dict[str, Any]:
        session_id = f"committee_{uuid.uuid4().hex[:12]}"
        row = {
            "dossier_id": dossier_id,
            "session_id": session_id,
            "title": title,
            "mode": mode,
            "active_section": active_section,
            "team": team,
            "status": "active",
        }
        created = self.db.insert("rnd_committee_sessions", row)
        return created[0] if isinstance(created, list) else created

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        rows = self.db.select(
            "rnd_committee_sessions",
            filters={"session_id": session_id},
            limit=1,
        )
        return rows[0] if rows else None

    def list_sessions(self, dossier_id: str, *, limit: int = 20) -> list[dict[str, Any]]:
        return self.db.select(
            "rnd_committee_sessions",
            filters={"dossier_id": dossier_id},
            order_by="created_at",
            limit=limit,
        )

    def get_active_session(self, dossier_id: str) -> dict[str, Any] | None:
        rows = self.db.select(
            "rnd_committee_sessions",
            filters={"dossier_id": dossier_id, "status": "active"},
            limit=1,
        )
        return rows[0] if rows else None

    def close_session(self, session_id: str) -> dict[str, Any] | None:
        session = self.get_session(session_id)
        if not session:
            return None
        self.db.update(
            "rnd_committee_sessions",
            session["id"],
            {"status": "closed", "closed_at": datetime.utcnow().isoformat()},
        )
        return self.get_session(session_id)

    def add_message(
        self,
        *,
        session_id: str,
        dossier_id: str,
        speaker: str,
        role: str,
        content: str,
        section_key: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        row = {
            "session_id": session_id,
            "dossier_id": dossier_id,
            "speaker": speaker,
            "role": role,
            "content": content,
            "section_key": section_key,
            "metadata": metadata,
        }
        created = self.db.insert("rnd_committee_messages", row)
        return created[0] if isinstance(created, list) else created

    def list_messages(self, session_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
        rows = self.db.select(
            "rnd_committee_messages",
            filters={"session_id": session_id},
            order_by="created_at",
            limit=limit,
        )
        return list(rows or [])


def get_committee_repository() -> RndCommitteeRepository:
    return RndCommitteeRepository()
