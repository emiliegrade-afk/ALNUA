"""Tests for COO agent intent detection — pure functions, no LLM."""

from __future__ import annotations


from agents.coo_agent import (
    _detect_research_intent,
    _detect_teach_intent,
    _format_plan_execution_result,
    _is_standalone_rnd_research,
    _needs_plan_execution,
    detect_coding_intent,
    detect_target_repo,
)


class TestCodingIntent:
    def test_detects_code_keyword(self) -> None:
        assert detect_coding_intent("Ajoute une feature sur le dashboard") is True

    def test_rejects_non_coding(self) -> None:
        assert detect_coding_intent("Quel est le statut du projet ?") is False


class TestTargetRepo:
    def test_nomad_keyword(self) -> None:
        assert detect_target_repo("Fix le bug Nuaway map") == "nomad"

    def test_hub_default(self) -> None:
        assert detect_target_repo("Corrige le middleware") == "hub"


class TestPlanExecution:
    def test_needs_execution_for_analysis(self) -> None:
        assert _needs_plan_execution("Fais une analyse de faisabilité pour NomadApp") is True

    def test_skips_brief_only(self) -> None:
        assert _needs_plan_execution("Qu'est-ce qui est urgent aujourd'hui ?") is False

    def test_format_success(self) -> None:
        result = {
            "title": "Test plan",
            "results": [
                {"agent_id": "pm", "description": "Brief", "success": True},
            ],
            "failure_count": 0,
        }
        text = _format_plan_execution_result(result)
        assert "✅" in text
        assert "pm" in text

    def test_format_error(self) -> None:
        text = _format_plan_execution_result({"error": "timeout", "results": []})
        assert "❌" in text


class TestResearchIntent:
    def test_detects_research(self) -> None:
        is_research, agent = _detect_research_intent("Fais une veille sur le marketing digital")
        assert is_research is True

    def test_rnd_standalone(self) -> None:
        assert _is_standalone_rnd_research("Lance un cycle R&D sur les tendances IA") is True
        assert _is_standalone_rnd_research("Recherche pour Nuaway vanlife") is False


class TestTeachIntent:
    def test_detects_teach(self) -> None:
        is_teach, agent, topic = _detect_teach_intent("Apprends à Nadia que le CEO préfère les mails courts")
        assert is_teach is True
