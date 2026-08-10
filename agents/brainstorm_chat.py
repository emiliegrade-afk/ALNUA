"""Brainstorm agent — conversational chat with project context."""
from __future__ import annotations

import json
from typing import Any

from agents.base import log_agent_action
from agents.brainstorm_constants import CHAT_SYSTEM_PROMPT
from skills.skill_langfuse import trace_agent


class BrainstormChatMixin:
    """Requires session + memory mixins and ``self.llm``, ``self.db``."""

    def _build_project_context(self, project_id: str | None) -> str:
        if not project_id:
            return (
                "\n\nContexte : ALNUA Global — vision multi-branches "
                "(App Naïa, Gaming Wyrdheim, Robotique Eve)."
            )

        project = self.db.select("projects", filters={"id": project_id})
        if not project:
            return "\n\nContexte : nouveau projet en exploration."

        p = project[0]
        roadmap = self.db.select("roadmap", filters={"project_id": project_id}, limit=5)
        feedback = self.db.select(
            "feedback",
            filters={"project_id": project_id},
            order_by="created_at",
            ascending=False,
            limit=5,
        )
        return f"""

Contexte projet actif :
- Nom : {p['name']}
- Branche : {p['branch']}
- Statut : {p['status']}
- Description : {p['description']}
- Roadmap récente : {json.dumps(roadmap, ensure_ascii=False)[:800]}
- Feedback récent : {json.dumps(feedback, ensure_ascii=False)[:800]}
"""

    def _history_to_messages(self, session_id: str) -> list[dict[str, str]]:
        session = self.get_session(session_id)
        history: list[dict[str, str]] = []
        for msg in session["messages"]:
            if msg["id"] == "welcome":
                continue
            history.append({"role": msg["role"], "content": msg["content"]})
        return history

    @trace_agent("brainstorm_agent")
    def chat(
        self,
        message: str,
        project_id: str | None = None,
        session_id: str | None = None,
    ) -> dict[str, Any]:
        message = message.strip()
        if not message:
            raise ValueError("Message vide")

        is_new = not session_id
        if is_new:
            session_id = self.create_session(
                project_id,
                title=message[:80],
            )

        system = CHAT_SYSTEM_PROMPT + self._build_project_context(project_id)

        from skills.skill_agent_learning import get_learning_context, record_task_learning

        mem0_block = get_learning_context("brainstorm", message)
        if mem0_block:
            system += mem0_block

        # Mémoire cross-sessions Supabase au premier message
        if is_new:
            memory = self.get_project_memory(project_id)
            if memory:
                system += f"\n\n{memory}"

        history = self._history_to_messages(session_id)
        history.append({"role": "user", "content": message})

        try:
            response = self.llm.chat(
                system=system,
                messages=history,
                agent_id="brainstorm",
                temperature=0.85,
                max_tokens=4096,
            )
            self.db.insert(
                "agent_logs",
                {
                    "agent_name": self.AGENT_NAME,
                    "action": "brainstorm_chat",
                    "project_id": project_id,
                    "input_summary": json.dumps(
                        {"session_id": session_id, "user": message},
                        ensure_ascii=False,
                    )[:2000],
                    "output_summary": response[:2000],
                    "status": "success",
                },
            )
            try:
                record_task_learning(
                    agent_id="brainstorm",
                    task=f"brainstorm {session_id}",
                    outcome=str({"response": response[:500], "session_id": session_id}),
                    success=True,
                )
            except Exception:
                pass
            return {"response": response, "session_id": session_id}
        except Exception as exc:
            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "brainstorm_chat",
                input_summary=message[:200],
                output_summary=str(exc),
                status="error",
                project_id=project_id,
            )
            raise
