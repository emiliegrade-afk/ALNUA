"""Tests security ingest orchestration."""

from __future__ import annotations

from unittest.mock import patch

from services.security_ops import run_security_ingest


def test_security_ingest_notifies(monkeypatch):
    monkeypatch.setenv("SECURITY_ALERT_EMAIL", "")
    with (
        patch("skills.skill_hub_notify.notify_hub", return_value={"telegram": True}) as notify,
        patch("skills.skill_error_journal.log_error", return_value="j-1") as log,
    ):
        result = run_security_ingest(
            {
                "type": "auth_failure_burst",
                "severity": "high",
                "title": "Burst auth",
                "detail": "test",
                "source": "resonance-api",
                "repo_slug": "resonance",
                "ipHash": "abc",
            }
        )
    assert result["success"] is True
    assert result["action"] == "ingested"
    assert result["journal_id"] == "j-1"
    notify.assert_called_once()
    log.assert_called_once()
