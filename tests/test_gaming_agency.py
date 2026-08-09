"""DEC-020 — Gaming studio agency (Claude Code on local UE project)."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

from skills import skill_gaming_agency as agency


def test_agency_status_not_configured(monkeypatch: Any) -> None:
    monkeypatch.delenv("UE_PROJECT_PATH", raising=False)
    monkeypatch.delenv("REPO_PATH_GAMING", raising=False)
    with patch(
        "skills.skill_ue58.ue58_health",
        return_value={"configured": False, "connected": False},
    ):
        out = agency.agency_status()
    assert out["ok"] is False
    assert out["configured"] is False
    assert "UE_PROJECT_PATH" in (out.get("error") or "") or "REPO_PATH" in (out.get("error") or "")


def test_run_rejects_unknown_agent(monkeypatch: Any, tmp_path: Path) -> None:
    monkeypatch.setenv("UE_PROJECT_PATH", str(tmp_path))
    (tmp_path / ".git").mkdir()
    out = agency.run_studio_task(
        agent_id="secretary",
        title="x",
        description="y",
    )
    assert out["ok"] is False
    assert "autorisé" in (out.get("error") or "").lower() or "non autorisé" in (out.get("error") or "").lower()


def test_run_requires_git(monkeypatch: Any, tmp_path: Path) -> None:
    monkeypatch.setenv("UE_PROJECT_PATH", str(tmp_path))
    out = agency.run_studio_task(
        agent_id="dev_gaming",
        title="Add BT",
        description="Create enemy BT",
    )
    assert out["ok"] is False
    assert "git" in (out.get("error") or "").lower()


def test_run_calls_coding_pipeline(monkeypatch: Any, tmp_path: Path) -> None:
    monkeypatch.setenv("UE_PROJECT_PATH", str(tmp_path))
    (tmp_path / ".git").mkdir()
    fake = {
        "success": True,
        "pr_url": "https://github.com/example/pr/1",
        "branch": "feat/test",
        "commit_sha": "abc",
        "claude_output": "done",
        "error": None,
        "backend": "hub",
    }
    with patch("skills.skill_coding_agent.execute_coding_task", return_value=fake) as mock_run:
        out = agency.run_studio_task(
            agent_id="ai_programmer",
            title="Enemy BT",
            description="Add a simple hostile BT",
        )
    assert out["ok"] is True
    assert out["pr_url"] == fake["pr_url"]
    spec = mock_run.call_args[0][0]
    assert spec["repo_path"] == str(tmp_path.resolve())
    assert spec["agent_id"] == "ai_programmer"
