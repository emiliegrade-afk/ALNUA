"""SAV Bot — customer support: FAQ matching and ticket creation."""

from __future__ import annotations

import logging
from typing import Any

from agents.base import LLMClient
from bots.base import log_bot_action
from database.supabase_client import SupabaseClient, get_supabase

logger = logging.getLogger(__name__)

BOT_NAME = "sav_bot"

FAQ_MATCH_PROMPT = """Tu es le bot SAV d'ALNUA. Voici la FAQ du projet :
{faq_entries}

Question utilisateur : {question}

Réponds en JSON :
{{
  "matched": true/false,
  "faq_id": "uuid or null",
  "answer": "string — réponse si match, sinon proposition de réponse générique",
  "needs_ticket": true/false,
  "ticket_title": "string or null",
  "ticket_description": "string or null"
}}"""


class SAVBot:
    def __init__(self, db: SupabaseClient | None = None, llm: LLMClient | None = None) -> None:
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()

    def get_faq(self, project_id: str) -> list[dict[str, Any]]:
        return self.db.select("faq", filters={"project_id": project_id, "active": True})

    def handle_question(self, project_id: str, question: str, author: str | None = None) -> dict[str, Any]:
        faq_entries = self.get_faq(project_id)
        faq_text = "\n".join(
            f"- [{f['id']}] Q: {f['question']}\n  R: {f['answer']}" for f in faq_entries
        ) or "Aucune FAQ disponible."

        from agents.base import parse_json_response

        raw = self.llm.complete(
            "Tu es le support client ALNUA. Réponds en JSON uniquement.",
            FAQ_MATCH_PROMPT.format(faq_entries=faq_text, question=question),
            temperature=0.2,
        )
        result = parse_json_response(raw)

        self.db.insert(
            "feedback",
            {
                "project_id": project_id,
                "source": "sav",
                "author": author,
                "content": question,
                "sentiment": "neutral",
                "status": "processed" if result.get("matched") else "new",
            },
        )

        if result.get("needs_ticket") and result.get("ticket_title"):
            ticket = self.db.insert(
                "tickets",
                {
                    "project_id": project_id,
                    "type": "bug" if "bug" in question.lower() else "improvement",
                    "priority": "medium",
                    "title": result["ticket_title"],
                    "description": result.get("ticket_description", question),
                    "source": "sav_bot",
                    "status": "open",
                },
            )
            result["ticket_id"] = ticket["id"]

        log_bot_action(
            self.db,
            BOT_NAME,
            "handle_question",
            input_summary=question[:200],
            output_summary=result.get("answer", "")[:200],
            project_id=project_id,
        )
        return result

    def add_faq_entry(
        self,
        project_id: str,
        question: str,
        answer: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        return self.db.insert(
            "faq",
            {
                "project_id": project_id,
                "question": question,
                "answer": answer,
                "tags": tags or [],
                "active": True,
            },
        )
