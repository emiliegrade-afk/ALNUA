"""Tests for NUAWAY bootstrap — Phase 7."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from services.nuaway_bootstrap import run_nuaway_bootstrap


@patch("shutil.which", side_effect=lambda cmd: "/usr/bin/gh" if cmd == "gh" else None)
@patch("config.github_repos.get_target_by_slug")
@patch("services.nuaway_readiness.generate_readiness_report")
def test_bootstrap_suggests_clone_when_no_nomad(mock_report, mock_target, _which) -> None:
    target = MagicMock()
    target.local_path.is_dir.return_value = False
    target.local_path.__str__ = lambda self: "C:\\Dev\\NUAWAY"  # type: ignore[method-assign]
    mock_target.return_value = target
    mock_report.return_value = {
        "beta_ready": False,
        "readiness_pct": 12.5,
        "missing_critical": ["Repo NUAWAY cloné localement"],
        "agents_gate": {"gate_open": False, "readiness_pct": 25},
    }

    result = run_nuaway_bootstrap(refresh=True)

    assert result["environment"]["nomad_cloned"] is False
    ids = [s["id"] for s in result["next_steps"]]
    assert "clone_nomad" in ids
    assert "claude_cli" in ids


@patch("shutil.which", return_value="/usr/bin/claude")
@patch("config.github_repos.get_target_by_slug")
@patch("services.nuaway_readiness.generate_readiness_report")
def test_bootstrap_beta_ready(mock_report, mock_target, _which) -> None:
    target = MagicMock()
    target.local_path.is_dir.return_value = True
    mock_target.return_value = target
    mock_report.return_value = {
        "beta_ready": True,
        "readiness_pct": 100,
        "missing_critical": [],
        "agents_gate": {"gate_open": True, "readiness_pct": 100},
    }

    result = run_nuaway_bootstrap(refresh=True)

    assert result["beta_ready"] is True
    assert any(s["id"] == "launch_beta" for s in result["next_steps"])
