"""Tests for CEO cockpit aggregator — Phase 5."""

from __future__ import annotations

from unittest.mock import patch

from services.ceo_cockpit import get_ceo_cockpit


@patch("skills.skill_gh_issues.list_ready_issues", return_value=[{"id": 1}, {"id": 2}])
@patch("agents.rnd_ceo_agent.RndCeoAgent")
@patch("services.production_ops.get_production_ops_status")
@patch("services.academy_progress.get_academy_status")
@patch("services.academy_gate.evaluate_academy_gate")
def test_get_ceo_cockpit_payload(
    mock_gate,
    mock_academy,
    mock_prod,
    mock_ceo_cls,
    mock_issues,
) -> None:
    mock_gate.return_value = {
        "gate_open": False,
        "readiness_pct": 37.5,
        "criteria": [
            {"id": "success_rate_65", "label": "Taux succès", "critical": True, "passed": False},
        ],
    }
    mock_academy.return_value = {"progress": {"current_level": 2}}
    mock_prod.return_value = {"open_errors": 1}
    mock_ceo_cls.return_value.list_ceo_queue.return_value = {
        "to_validate": [{"id": "d1", "title": "Dossier test"}],
        "to_prepare": [],
    }

    payload = get_ceo_cockpit()

    assert "headline" in payload
    assert payload["academy_gate"]["readiness_pct"] == 37.5
    assert payload["academy"]["progress"]["current_level"] == 2
    assert payload["production_ops"]["open_errors"] == 1
    assert len(payload["ceo_queue"]["to_validate"]) == 1
    assert payload["pipeline"]["agent_ready_count"] == 2
    assert "Academy" in payload["headline"] or "37.5" in payload["headline"]


@patch("skills.skill_gh_issues.list_ready_issues", side_effect=RuntimeError("gh down"))
@patch("agents.rnd_ceo_agent.RndCeoAgent", side_effect=RuntimeError("ceo down"))
@patch("services.production_ops.get_production_ops_status", side_effect=RuntimeError("ops down"))
@patch("services.academy_progress.get_academy_status", side_effect=RuntimeError("academy down"))
@patch("services.academy_gate.evaluate_academy_gate", side_effect=RuntimeError("gate down"))
def test_get_ceo_cockpit_degrades_silently(*_mocks) -> None:
    payload = get_ceo_cockpit()

    assert "headline" in payload
    assert "error" in payload["academy_gate"]
    assert payload["pipeline"]["agent_ready_count"] == 0
