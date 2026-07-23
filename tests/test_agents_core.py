"""Smoke tests for core agents — mocked LLM."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agents.qa_agent import QAAgent
from agents.pm_agent import PMAgent
from agents.spec_agent import SpecAgent


class MockLLM:
    def complete(self, system: str, user: str, **kwargs: object) -> str:
        if "tickets" in user.lower() or "feedback" in user.lower():
            return '{"tickets": [], "summary": "RAS"}'
        return '{"status": "ok", "summary": "done"}'


@pytest.fixture()
def mock_db() -> MagicMock:
    db = MagicMock()
    db.select.return_value = []
    return db


class TestQAAgent:
    def test_agent_identity(self, mock_db: MagicMock) -> None:
        agent = QAAgent(db=mock_db, llm=MockLLM())
        assert agent.AGENT_NAME == "qa_agent"

    def test_analyze_feedback_empty(self, mock_db: MagicMock) -> None:
        mock_db.select.return_value = []
        agent = QAAgent(db=mock_db, llm=MockLLM())
        result = agent.analyze_feedback_batch("proj-1", limit=5)
        assert result["summary"] == "Aucun feedback nouveau à analyser."
        assert result["tickets"] == []


class TestPMAgent:
    def test_agent_identity(self, mock_db: MagicMock) -> None:
        agent = PMAgent(db=mock_db, llm=MockLLM())
        assert agent.AGENT_NAME == "pm_agent"

    def test_has_triage_method(self, mock_db: MagicMock) -> None:
        agent = PMAgent(db=mock_db, llm=MockLLM())
        assert hasattr(agent, "triage_project")


class TestSpecAgent:
    def test_agent_identity(self, mock_db: MagicMock) -> None:
        agent = SpecAgent(db=mock_db, llm=MockLLM())
        assert agent.AGENT_NAME == "spec_agent"
