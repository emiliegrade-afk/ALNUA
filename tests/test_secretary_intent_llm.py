"""Tests — Nadia LLM intent classifier (Lot A)."""

from __future__ import annotations

from unittest.mock import patch

from services.secretary_intent_llm import (
    INTENT_VALUES,
    classify_secretary_intent,
    should_dispatch_tool,
)


def test_should_dispatch_conversation_always():
    assert should_dispatch_tool("conversation", 0.1) is True


def test_should_dispatch_tool_needs_confidence():
    assert should_dispatch_tool("email", 0.4) is False
    assert should_dispatch_tool("email", 0.7) is True


def test_classify_paraphrase_wake_ops():
    fake = {
        "intent": "wake_ops",
        "confidence": 0.9,
        "slots": {},
        "reason": "remets theo au boulot",
    }
    with patch("services.secretary_intent_llm.LLMClient") as llm_cls:
        llm_cls.return_value.complete.return_value = "{}"
        with patch(
            "services.secretary_intent_llm.parse_json_response",
            return_value=fake,
        ):
            out = classify_secretary_intent("remets Théo au boulot sur les exercices")
    assert out["intent"] == "wake_ops"
    assert out["intent"] in INTENT_VALUES
    assert "weather" in INTENT_VALUES


def test_classify_failure_falls_back_to_conversation():
    with patch("services.secretary_intent_llm.LLMClient", side_effect=RuntimeError("down")):
        out = classify_secretary_intent("bonjour ça va")
    assert out["intent"] == "conversation"


def test_classify_failure_keyword_weather():
    with patch("services.secretary_intent_llm.LLMClient", side_effect=RuntimeError("down")):
        out = classify_secretary_intent("météo à Paris")
    assert out["intent"] == "weather"
    assert out["confidence"] >= 0.55


def test_dispatch_ask_lawyer_intent():
    from agents.secretary_instruction import SecretaryInstructionMixin

    class _Agent(SecretaryInstructionMixin):
        AGENT_NAME = "secretary"
        db = None

        def _handle_ask_lawyer(self, instruction: str, *, session_id: str = "hub") -> str:
            return "LEGAL_OK"

    agent = _Agent()
    with patch(
        "services.secretary_intent_llm.classify_secretary_intent",
        return_value={"intent": "ask_lawyer", "confidence": 0.95, "slots": {}, "reason": "t"},
    ):
        out = agent.handle_instruction("fais relire ce NDA")
    assert out == "LEGAL_OK"


def test_handle_instruction_uses_llm_intent_for_email():
    from agents.secretary_instruction import SecretaryInstructionMixin

    class _Agent(SecretaryInstructionMixin):
        AGENT_NAME = "secretary"
        db = None

        def _handle_email_nl(self, instruction: str, *, session_id: str = "hub") -> str:
            return "Email draft OK"

    agent = _Agent()
    with patch(
        "services.secretary_intent_llm.classify_secretary_intent",
        return_value={"intent": "email", "confidence": 0.9, "slots": {}, "reason": "t"},
    ):
        out = agent.handle_instruction("prépare un message pour le partenaire")
    assert out == "Email draft OK"
