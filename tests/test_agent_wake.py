"""Tests for agent wake / pipeline status."""

from __future__ import annotations

from services.agent_wake import _format_wake_summary, get_pipeline_status


def test_format_wake_summary_queued() -> None:
    status = {
        "message": "Aucune tâche en file.",
        "academy": {"current_level": 2, "completed": 10, "total": 52},
    }
    queued = {"marked_count": 2, "marked": [{"number": 25}, {"number": 26}]}
    text = _format_wake_summary(status, queued, [])
    assert "#25" in text
    assert "2 issue" in text


def test_pipeline_status_shape() -> None:
    # May return unconfigured if GITHUB_REPO_ACADEMY absent in CI
    result = get_pipeline_status()
    assert "verdict" in result
    assert result["verdict"] in ("working", "idle", "stuck", "unconfigured")
