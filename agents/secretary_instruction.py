"""Secretary agent — natural-language instruction router (LLM-first)."""
from __future__ import annotations

from agents.base import log_agent_action
from skills.skill_agent_learning import record_task_learning
from skills.skill_langfuse import trace_agent


class SecretaryInstructionMixin:
    """Requires handler mixins and ``AgentBase`` wiring."""

    @trace_agent("secretary")
    def handle_instruction(self, instruction: str, *, session_id: str = "hub") -> str:
        """
        Point d'entrée langage naturel — Telegram, Hub, desktop.
        Intent LLM d'abord ; mots-clés seulement pour confirmations critiques.
        """
        instruction = instruction.strip()
        if not instruction:
            return (
                "Je suis là — parle-moi normalement : mails, agenda, contrats, "
                "recherches, brief du jour, ou n'importe quelle question."
            )

        from services.secretary_intent_llm import (
            classify_secretary_intent,
            should_dispatch_tool,
        )
        from services.secretary_intents import detect_send_confirm

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

        # Safety: explicit send confirm stays keyword-gated (évite envoi accidentel)
        if detect_send_confirm(instruction):
            return self._handle_send_confirm(session_id)

        classified = classify_secretary_intent(instruction)
        intent = str(classified.get("intent") or "conversation")
        confidence = float(classified.get("confidence") or 0.0)

        if not should_dispatch_tool(intent, confidence):
            intent = "conversation"

        return self._dispatch_intent(intent, instruction, session_id=session_id)

    def _dispatch_intent(self, intent: str, instruction: str, *, session_id: str) -> str:
        from services.secretary_intents import (
            build_academy_status_brief,
            build_morning_brief_for_secretary,
            build_night_report,
        )

        tg_chat = session_id.removeprefix("tg:") if session_id.startswith("tg:") else None

        if intent == "connect":
            return self._handle_connect_nl(instruction)
        if intent == "inbox":
            return self._handle_inbox_nl(instruction)
        if intent == "calendar":
            return self._handle_calendar_nl(instruction)
        if intent == "night_report":
            report = build_night_report()
            self._finish_instruction(instruction, report)
            return report
        if intent == "briefing":
            brief = build_morning_brief_for_secretary()
            self._finish_instruction(instruction, brief[:200])
            return brief
        if intent == "wake_ops":
            return self._handle_wake_ops(instruction)
        if intent == "research":
            return self._handle_research(instruction, session_id=session_id)
        if intent == "aria_delegation":
            return self._handle_aria_delegation(instruction)
        if intent == "academy":
            brief = build_academy_status_brief()
            self._finish_instruction(instruction, brief[:200])
            return brief
        if intent == "email":
            return self._handle_email_nl(instruction, session_id=session_id)
        if intent == "contract":
            return self._handle_contract_nl(instruction)
        if intent == "meeting":
            return self._handle_meeting_nl(instruction, session_id=session_id)
        if intent == "ask_lawyer":
            return self._handle_ask_lawyer(instruction, session_id=session_id)
        if intent == "write_doc":
            return self._handle_write_doc(instruction, session_id=session_id)
        if intent == "housekeep":
            return self._handle_housekeep(instruction, session_id=session_id)
        if intent == "send_confirm":
            return self._handle_send_confirm(session_id)

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
