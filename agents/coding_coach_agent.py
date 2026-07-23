"""Coding Coach Agent — Luca Bernard, Prof de code ALNUA (CEO Emilie)."""

from __future__ import annotations

from agents.agent_base import AgentBase

import logging
from typing import Any

from agents.base import log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from skills.skill_langfuse import trace_agent
from services.hermes_skills import inject_hermes_context

logger = logging.getLogger(__name__)


class CodingCoachAgent(AgentBase):
    AGENT_NAME = "coding_coach"

    SYSTEM_PROMPT = get_system_prompt("coding_coach")


    @trace_agent("coding_coach")
    def teach(
        self,
        message: str,
        *,
        workspace: str = "sandbox",
        file_path: str | None = None,
        file_content: str | None = None,
    ) -> str:
        ctx = f"Workspace IDE : {workspace}\n"
        if file_path and file_content is not None:
            snippet = file_content[:6000]
            if len(file_content) > 6000:
                snippet += "\n… [fichier tronqué]"
            ctx += f"Fichier ouvert : {file_path}\n```\n{snippet}\n```\n"

        prompt = inject_learning_context(
            f"""{ctx}
Question d'Emilie :
{message.strip()}

Réponds comme son prof — pédagogique, concret, encourageant.""",
            self.AGENT_NAME,
            message[:80],
        )
        raw = self._complete(
            prompt,
            system_prompt=inject_hermes_context("coach", self.SYSTEM_PROMPT, max_chars=5000),
            temperature=0.5,
        )
        try:
            parsed = parse_json_response(raw)
            if isinstance(parsed, dict) and parsed.get("reply"):
                reply = str(parsed["reply"])
            else:
                reply = raw.strip()
        except Exception:
            reply = raw.strip()

        log_agent_action(
            self.db,
            self.AGENT_NAME,
            "teach",
            input_summary=message[:100],
            output_summary=reply[:100],
        )
        try:
            record_task_learning(self.AGENT_NAME, "teach", reply[:300], success=True)
        except Exception:
            pass
        return reply

    @trace_agent("coding_coach")
    def suggest_exercise(self, topic: str, level: str = "débutant") -> dict[str, Any]:
        prompt = inject_learning_context(
            f"""Propose un exercice de code pour Emilie.
Sujet : {topic}
Niveau : {level}
Workspace : bac à sable (fichiers isolés)

JSON :
{{
  "title": "titre court",
  "instructions": "énoncé clair",
  "starter_file": "hello.py",
  "starter_code": "code de départ",
  "hints": ["indice 1", "indice 2"],
  "success_criteria": "comment savoir que c'est bon"
}}""",
            self.AGENT_NAME,
            topic,
        )
        raw = self._complete(prompt, temperature=0.4)
        result = parse_json_response(raw)
        log_agent_action(
            self.db,
            self.AGENT_NAME,
            "suggest_exercise",
            input_summary=topic[:80],
            output_summary=str(result.get("title", ""))[:80],
        )
        return result
