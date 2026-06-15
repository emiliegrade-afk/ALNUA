"""Tests for Sentry ops (Phase 4)."""

from __future__ import annotations

import hashlib
import hmac
import json
from unittest.mock import patch

from services.sentry_ops import (
    SentryIngestEvent,
    format_hotfix_issue_body,
    ingest_sentry_event,
    parse_sentry_webhook,
    resolve_repo_slug_from_sentry,
    verify_sentry_signature,
)


def test_verify_sentry_signature():
    body = b'{"action":"created"}'
    secret = "test-secret"
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    assert verify_sentry_signature(body, sig, secret) is True
    assert verify_sentry_signature(body, "bad", secret) is False
    assert verify_sentry_signature(body, None, "") is False
    assert verify_sentry_signature(body, None, "", allow_unsigned=True) is True
    assert verify_sentry_signature(body, None, secret) is False


def test_parse_sentry_issue_alert():
    payload = {
        "action": "created",
        "data": {
            "issue": {
                "id": "123",
                "title": "TypeError in HomeScreen",
                "culprit": "app/screens/Home.tsx",
                "level": "error",
                "permalink": "https://sentry.io/issues/123",
                "project": {"slug": "nuaway"},
            },
            "event": {
                "event_id": "evt-1",
                "platform": "javascript",
                "tags": [["environment", "production"]],
                "message": "Cannot read property map",
            },
        },
    }
    event = parse_sentry_webhook(payload)
    assert event is not None
    assert event.title == "TypeError in HomeScreen"
    assert event.environment == "production"
    assert event.project_slug == "nuaway"


def test_parse_sentry_resolved_ignored():
    assert parse_sentry_webhook({"action": "resolved", "data": {}}) is None


def test_resolve_repo_slug_nomad(monkeypatch):
    monkeypatch.setenv("GITHUB_REPO_NOMAD", "org/nomad")
    from config.github_repos import get_repo_targets

    get_repo_targets.cache_clear()
    event = SentryIngestEvent(
        fingerprint="abc",
        title="Crash",
        message="err",
        project_slug="nuaway",
    )
    assert resolve_repo_slug_from_sentry(event) == "nomad"
    get_repo_targets.cache_clear()


def test_format_hotfix_issue_body():
    event = SentryIngestEvent(
        fingerprint="fp1",
        title="API 500",
        message="Internal error",
        culprit="api/routes/users.py",
        permalink="https://sentry.io/1",
    )
    body = format_hotfix_issue_body(
        event, repo_slug="hub", github_repo="org/hub", journal_id="j-1"
    )
    assert "## Description" in body
    assert "j-1" in body
    assert "python_fastapi" in body


@patch("services.sentry_ops.create_hotfix_github_issue")
@patch("services.sentry_ops.log_error")
def test_ingest_dedup(mock_log, mock_issue, tmp_path, monkeypatch):
    monkeypatch.setenv("SENTRY_AUTO_ISSUE", "false")
    dedup_file = tmp_path / "sentry_ingest.json"
    monkeypatch.setattr("services.sentry_ops._DEDUP_PATH", dedup_file)

    mock_log.return_value = "journal-1"
    event = SentryIngestEvent(
        fingerprint="dedup-fp",
        title="First",
        message="boom",
    )
    r1 = ingest_sentry_event(event, create_issue=False)
    assert r1["action"] == "ingested"
    r2 = ingest_sentry_event(event, create_issue=False)
    assert r2["action"] == "dedup_skipped"
    mock_log.assert_called_once()
