"""Brainstorm agent — session storage via agent_logs."""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any

from agents.brainstorm_constants import WELCOME_MESSAGE


class BrainstormSessionMixin:
    """Requires ``self.db``, ``self.AGENT_NAME``, ``self.SESSION_ACTIONS``."""

    @staticmethod
    def _parse_input(raw: str) -> dict[str, Any]:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"session_id": None, "user": raw}

    def _fetch_brainstorm_logs(self, limit: int = 500) -> list[dict[str, Any]]:
        logs = self.db.select(
            "agent_logs",
            filters={"agent_name": self.AGENT_NAME},
            order_by="created_at",
            ascending=True,
            limit=limit,
        )
        return [log for log in logs if log.get("action") in self.SESSION_ACTIONS]

    def list_sessions(self, limit: int = 30) -> list[dict[str, Any]]:
        logs = self._fetch_brainstorm_logs(limit=500)
        sessions: dict[str, dict[str, Any]] = {}

        for log in logs:
            meta = self._parse_input(log.get("input_summary", "{}"))
            session_id = meta.get("session_id")
            if not session_id:
                continue

            if session_id not in sessions:
                title = meta.get("title") or meta.get("user") or "Session brainstorm"
                sessions[session_id] = {
                    "session_id": session_id,
                    "title": str(title)[:80],
                    "project_id": log.get("project_id"),
                    "created_at": log.get("created_at"),
                    "updated_at": log.get("created_at"),
                    "message_count": 0,
                }

            sessions[session_id]["updated_at"] = log.get("created_at")
            if log.get("action") == "brainstorm_chat":
                sessions[session_id]["message_count"] += 1
                if meta.get("user") and sessions[session_id]["title"] == "Session brainstorm":
                    sessions[session_id]["title"] = str(meta["user"])[:80]

        result = sorted(
            sessions.values(),
            key=lambda s: s.get("updated_at") or "",
            reverse=True,
        )
        return result[:limit]

    def get_session(self, session_id: str) -> dict[str, Any]:
        logs = self._fetch_brainstorm_logs()
        messages: list[dict[str, Any]] = []
        project_id: str | None = None
        found = False

        for log in logs:
            meta = self._parse_input(log.get("input_summary", "{}"))
            if meta.get("session_id") != session_id:
                continue

            found = True
            if log.get("project_id"):
                project_id = log["project_id"]

            if log.get("action") == "session_start":
                continue

            user_text = meta.get("user", "")
            assistant_text = log.get("output_summary", "")
            if user_text:
                messages.append(
                    {
                        "id": f"{log['id']}-user",
                        "role": "user",
                        "content": user_text,
                        "created_at": log.get("created_at"),
                    }
                )
            if assistant_text:
                messages.append(
                    {
                        "id": f"{log['id']}-assistant",
                        "role": "assistant",
                        "content": assistant_text,
                        "created_at": log.get("created_at"),
                    }
                )

        if not found:
            raise ValueError(f"Session {session_id} not found")

        if not messages:
            messages.append(
                {
                    "id": "welcome",
                    "role": "assistant",
                    "content": WELCOME_MESSAGE,
                    "created_at": datetime.utcnow().isoformat(),
                }
            )

        return {
            "session_id": session_id,
            "project_id": project_id,
            "messages": messages,
        }

    def create_session(self, project_id: str | None = None, title: str = "Nouvelle session") -> str:
        session_id = str(uuid.uuid4())
        self.db.insert(
            "agent_logs",
            {
                "agent_name": self.AGENT_NAME,
                "action": "session_start",
                "project_id": project_id,
                "input_summary": json.dumps(
                    {"session_id": session_id, "title": title},
                    ensure_ascii=False,
                )[:2000],
                "output_summary": WELCOME_MESSAGE[:2000],
                "status": "success",
            },
        )
        return session_id
