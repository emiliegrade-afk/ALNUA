"""Tests for NUAWAY beta readiness — Phase 6."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from services.nuaway_readiness import (
    BETA_LAUNCH_CHECKLIST,
    evaluate_beta_readiness,
    generate_readiness_report,
    set_ceo_beta_go,
)


def test_beta_checklist_count() -> None:
    assert len(BETA_LAUNCH_CHECKLIST) == 8
    critical = [c for c in BETA_LAUNCH_CHECKLIST if c.get("critical")]
    assert len(critical) == 6


@patch("services.nuaway_readiness.save_readiness_state")
@patch("services.nuaway_readiness.load_readiness_state", return_value={"ceo_beta_go": True})
@patch("services.nuaway_readiness._beta_portal_ok", return_value=True)
@patch("services.nuaway_readiness._nomad_local_path")
@patch("services.academy_progress.load_progress")
@patch("services.sentry_ops._load_dedup", return_value={"recent": [{"id": 1}]})
@patch("services.nuaway_gate.evaluate_nuaway_gate")
def test_evaluate_beta_all_pass(
    mock_gate,
    mock_dedup,
    mock_prog,
    mock_nomad,
    mock_portal,
    mock_state,
    mock_save,
) -> None:
    mock_gate.return_value = {
        "gate_open": True,
        "readiness_pct": 100,
        "metrics": {"build_issues_created": 10, "github_repo": "org/NUAWAY"},
        "ceo_dossier": {
            "ceo_status": "approved",
            "ceo_package_json": {
                "engineering_spec": {
                    "task_breakdown": [{"id": "T-1"}] * 6,
                    "qa_verdict": "approved",
                }
            },
        },
    }
    mock_prog.return_value = {
        "levels": {"4": {"done": 20, "total": 20, "failed": 0}},
    }
    local = MagicMock()
    local.is_dir.return_value = True
    mock_nomad.return_value = local

    result = evaluate_beta_readiness(refresh_gate=True)

    assert result["beta_ready"] is True
    assert result["critical_passed"] == result["critical_total"]
    assert result["passed"] == 8


@patch("services.nuaway_readiness.save_readiness_state")
@patch("services.nuaway_readiness.load_readiness_state")
@patch("services.nuaway_readiness._beta_portal_ok", return_value=False)
@patch("services.nuaway_readiness._nomad_local_path", return_value=None)
@patch("services.academy_progress.load_progress", return_value={"levels": {"4": {"done": 0, "total": 20, "failed": 2}}})
@patch("services.sentry_ops._load_dedup", return_value={})
@patch("services.nuaway_gate.evaluate_nuaway_gate")
def test_evaluate_beta_locked(mock_gate, *_mocks) -> None:
    mock_gate.return_value = {
        "gate_open": False,
        "readiness_pct": 25,
        "metrics": {"build_issues_created": 0},
        "ceo_dossier": None,
    }

    result = evaluate_beta_readiness(refresh_gate=False)

    assert result["beta_ready"] is False
    assert len(result["missing_critical"]) >= 3


@patch("services.nuaway_readiness.evaluate_beta_readiness")
@patch("services.nuaway_readiness.save_readiness_state")
@patch("services.nuaway_readiness.load_readiness_state", return_value={})
def test_generate_report_has_markdown(mock_load, mock_save, mock_eval) -> None:
    mock_eval.return_value = {
        "beta_ready": False,
        "readiness_pct": 50,
        "passed": 4,
        "total": 8,
        "criteria": [],
        "missing_critical": ["Repo NUAWAY cloné localement"],
        "agents_gate": {"gate_open": False, "readiness_pct": 25},
        "ceo_beta": {"approved": False},
        "evaluated_at": "2026-06-14T00:00:00+00:00",
    }

    report = generate_readiness_report(refresh_gate=False)

    assert "markdown" in report
    assert "Rapport readiness NUAWAY" in report["markdown"]
    assert report["headline"]
    mock_save.assert_called_once()


@patch("services.nuaway_readiness.evaluate_beta_readiness", return_value={"beta_ready": True})
@patch("services.nuaway_readiness.save_readiness_state")
@patch("services.nuaway_readiness.load_readiness_state")
def test_set_ceo_beta_go(mock_load, mock_save, mock_eval) -> None:
    mock_load.return_value = {"ceo_beta_go": False, "ceo_beta_note": ""}
    set_ceo_beta_go(approved=True, note="Test go")

    mock_save.assert_called_once()
    saved = mock_save.call_args[0][0]
    assert saved["ceo_beta_go"] is True
    assert saved["ceo_beta_note"] == "Test go"
    mock_eval.assert_called_once()
