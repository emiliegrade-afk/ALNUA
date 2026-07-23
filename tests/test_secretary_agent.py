"""Tests for secretary agent + intents — mocked LLM, no network."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from agents.secretary_agent import SecretaryAgent
from services import secretary_intents as intents


class MockLLM:
    def complete(self, system: str, user: str, **kwargs: object) -> str:
        lower = user.lower()
        if "emails entrants" in lower or "classe-les par priorité" in lower:
            return '{"urgent": [], "normal": [], "low": [], "spam_or_ignore": []}'
        if "email" in lower or "mail" in lower:
            return '{"subject": "Test", "body": "Corps test", "suggested_send_time": "matin"}'
        return '{"reply": "OK", "message": "Compris."}'


@pytest.fixture()
def agent() -> SecretaryAgent:
    return SecretaryAgent(db=MagicMock(), llm=MockLLM())


class TestSecretaryIntents:
    def test_night_report(self) -> None:
        assert intents.detect_night_report("rapport de la nuit academy") is True

    def test_briefing(self) -> None:
        assert intents.detect_briefing("briefing du jour") is True

    def test_email_intent(self) -> None:
        assert intents.detect_email_intent("rédige un mail à partenaire@x.com") is True

    def test_connect_intent(self) -> None:
        assert intents.detect_connect_intent("connecte mon gmail") is True

    def test_send_confirm(self) -> None:
        assert intents.detect_send_confirm("envoie le mail") is True

    def test_aria_delegation(self) -> None:
        assert intents.detect_aria_delegation("demande à aria de prioriser") is True


class TestSecretaryAgent:
    def test_draft_email_parses_json(self, agent: SecretaryAgent) -> None:
        result = agent.draft_email(
            subject="Relance",
            context="Partenaire en attente",
            recipient="test@example.com",
        )
        assert result["subject"] == "Test"
        assert "body" in result

    def test_triage_emails(self, agent: SecretaryAgent) -> None:
        result = agent.triage_emails([
            {"from": "a@b.com", "subject": "Urgent", "body": "Help"},
        ])
        assert "urgent" in result

    def test_handle_instruction_email_routing(self, agent: SecretaryAgent) -> None:
        with patch.object(agent, "_handle_email_nl", return_value="Email draft OK") as mock:
            out = agent.handle_instruction("rédige un mail à client@corp.com pour relance")
        assert out == "Email draft OK"
        mock.assert_called_once()

    def test_telegram_chat_id_parsing(self) -> None:
        assert SecretaryAgent._telegram_chat_id("tg:12345") == 12345
        assert SecretaryAgent._telegram_chat_id("hub") is None
