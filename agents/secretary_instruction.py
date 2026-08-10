"""Secretary agent — natural-language instruction router."""
from __future__ import annotations

from agents.base import log_agent_action
from skills.skill_agent_learning import record_task_learning
from skills.skill_langfuse import trace_agent


class SecretaryInstructionMixin:
    """Requires handler mixins and ``AgentBase`` wiring."""

    @trace_agent("secretary")
    def handle_instruction(self, instruction: str, *, session_id: str = "hub") -> str:
        """
        Point d'entrée langage naturel pour Emilie — Telegram et Hub.
        session_id isolates pending email drafts (hub vs Telegram chat).
        """
        instruction = instruction.strip()
        if not instruction:
            return "Je suis là — dis-moi ce dont tu as besoin (ton mail, ton planning, contrat, rapport de nuit, Academy…)."

        from services.secretary_intents import (
            build_academy_status_brief,
            build_morning_brief_for_secretary,
            build_night_report,
            detect_academy_intent,
            detect_aria_delegation,
            detect_briefing,
            detect_calendar_intent,
            detect_connect_intent,
            detect_contract_intent,
            detect_email_intent,
            detect_inbox_intent,
            detect_meeting_intent,
            detect_night_report,
            detect_research_intent,
            detect_send_confirm,
            detect_wake_ops,
        )

        try:
            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "handle_instruction",
                input_summary=instruction[:120],
                output_summary="en cours",
                status="pending",
            )
        except Exception:
            pass

        if detect_send_confirm(instruction):
            return self._handle_send_confirm(session_id)

        if detect_connect_intent(instruction):
            return self._handle_connect_nl(instruction)

        if detect_inbox_intent(instruction):
            return self._handle_inbox_nl(instruction)

        if detect_calendar_intent(instruction):
            return self._handle_calendar_nl(instruction)

        if detect_night_report(instruction):
            report = build_night_report()
            self._finish_instruction(instruction, report)
            return report

        if detect_briefing(instruction):
            brief = build_morning_brief_for_secretary()
            self._finish_instruction(instruction, brief[:200])
            return brief

        if detect_wake_ops(instruction):
            return self._handle_wake_ops(instruction)

        if detect_research_intent(instruction):
            return self._handle_research(instruction, session_id=session_id)

        if detect_aria_delegation(instruction):
            return self._handle_aria_delegation(instruction)

        if detect_academy_intent(instruction):
            brief = build_academy_status_brief()
            self._finish_instruction(instruction, brief[:200])
            return brief

        if detect_email_intent(instruction):
            return self._handle_email_nl(instruction, session_id=session_id)

        if detect_contract_intent(instruction):
            return self._handle_contract_nl(instruction)

        if detect_meeting_intent(instruction):
            return self._handle_meeting_nl(instruction, session_id=session_id)

        tg_chat = session_id.removeprefix("tg:") if session_id.startswith("tg:") else None
        return self._handle_conversation(instruction, chat_id=tg_chat)

    def _finish_instruction(self, instruction: str, output: str) -> None:
        try:
            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "handle_instruction",
                input_summary=instruction[:120],
                output_summary=output[:200],
                status="success",
            )
            record_task_learning(self.AGENT_NAME, "handle_instruction", output[:300], success=True)
        except Exception:
            pass
