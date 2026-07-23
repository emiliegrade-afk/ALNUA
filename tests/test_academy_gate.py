"""Tests for Academy gate (Academy → Lounge) — Phase 5."""

from __future__ import annotations

from unittest.mock import patch

from services.academy_gate import GATE_DEFINITIONS, evaluate_academy_gate


def test_gate_definitions_shape() -> None:
    assert len(GATE_DEFINITIONS) == 8
    critical = [g for g in GATE_DEFINITIONS if g.get("critical")]
    assert len(critical) == 5
    ids = {g["id"] for g in GATE_DEFINITIONS}
    assert "success_rate_65" in ids
    assert "error_journal_top5" in ids
    assert "github_pipeline" in ids


@patch("services.academy_gate._lounge_product_ready", return_value=True)
@patch("services.academy_gate._academy_pipeline_ok", return_value=True)
@patch("services.academy_progress.save_progress")
@patch("services.academy_progress.load_progress", return_value={"gate_academy": {}})
@patch("services.academy_gate._sentry_ops_active", return_value=True)
@patch("services.academy_gate._lounge_build_manifest", return_value={"issues_created": 3, "slug": "lounge"})
@patch("services.academy_gate._mem0_lesson_count", return_value=40)
@patch("services.academy_gate._count_resolved_errors", return_value=6)
@patch("services.academy_progress.get_academy_status")
def test_evaluate_gate_all_critical_pass(
    mock_academy,
    _count,
    _mem0,
    _build,
    _sentry,
    _load,
    _save,
    _pipe,
    _lounge,
) -> None:
    mock_academy.return_value = {
        "progress": {
            "gate_academy": {
                "success_rate_65": True,
                "academy_n4_stable": True,
                "mem0_lessons_35": True,
            },
            "success_rate_pct": 70,
        }
    }

    result = evaluate_academy_gate(refresh_academy=True)

    assert result["gate_open"] is True
    assert result["critical_passed"] == result["critical_total"]
    assert result["readiness_pct"] == 100.0
    assert len(result["criteria"]) == 8


@patch("services.academy_gate._academy_pipeline_ok", return_value=False)
@patch("services.academy_gate._lounge_product_ready", return_value=False)
@patch("services.academy_progress.save_progress")
@patch("services.academy_progress.load_progress", return_value={"gate_academy": {}})
@patch("services.academy_gate._sentry_ops_active", return_value=False)
@patch("services.academy_gate._lounge_build_manifest", return_value={})
@patch("services.academy_gate._mem0_lesson_count", return_value=0)
@patch("services.academy_gate._count_resolved_errors", return_value=0)
@patch("services.academy_progress.get_academy_status")
def test_evaluate_gate_locked(mock_academy, *_mocks) -> None:
    mock_academy.return_value = {
        "progress": {
            "gate_academy": {
                "success_rate_65": False,
                "academy_n4_stable": False,
                "mem0_lessons_35": False,
            },
        }
    }

    result = evaluate_academy_gate(refresh_academy=True)

    assert result["gate_open"] is False
    assert result["critical_passed"] < result["critical_total"]
    failed_critical = [
        c for c in result["criteria"] if c["critical"] and not c["passed"]
    ]
    assert len(failed_critical) >= 3


def test_legacy_gate_nuaway_migrates_on_load() -> None:
    from services.academy_progress import _migrate_gate_keys

    data = {"gate_nuaway": {"success_rate_65": True}}
    migrated = _migrate_gate_keys(data)
    assert "gate_academy" in migrated
    assert "gate_nuaway" not in migrated
    assert migrated["gate_academy"]["success_rate_65"] is True
