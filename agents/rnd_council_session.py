"""R&D council agent — session lifecycle."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from agents.rnd_council_constants import COUNCIL_MEMBERS, SessionKind

logger = logging.getLogger(__name__)


class RndCouncilSessionMixin:
    """Requires ``self.db`` from ``RndCouncilAgent``."""

    def start_session(
        self,
        *,
        kind: SessionKind,
        topic: str = "",
        idea_id: str | None = None,
        structured_input: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session_id = f"council_{uuid.uuid4().hex[:12]}"
        title = topic.strip() or ("Évaluation structurée" if kind == "evaluation" else "Conseil stratégique")
        row = {
            "session_id": session_id,
            "dossier_id": None,
            "session_kind": kind,
            "idea_id": idea_id,
            "structured_input": structured_input,
            "topic": title,
            "title": title,
            "mode": "free",
            "team": [{"agent_id": k, "name": v["name"], "role": v["role"]} for k, v in COUNCIL_MEMBERS.items()],
            "status": "active",
        }
        session = self.db.insert("rnd_committee_sessions", row)
        logger.info("[RndCouncil] session %s créée (kind=%s)", session_id, kind)
        return session

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        rows = self.db.select("rnd_committee_sessions", filters={"session_id": session_id}, limit=1)
        return rows[0] if rows else None

    def list_messages(self, session_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
        return list(
            self.db.select(
                "rnd_committee_messages",
                filters={"session_id": session_id},
                order_by="created_at",
                limit=limit,
            )
            or []
        )

    def _next_round_index(self, session_id: str) -> int:
        rows = self.db.select(
            "rnd_committee_votes",
            filters={"session_id": session_id},
            order_by="round_index",
            ascending=False,
            limit=1,
        )
        if not rows:
            return 0
        return int(rows[0]["round_index"]) + 1
