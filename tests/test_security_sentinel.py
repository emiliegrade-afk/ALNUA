"""Tests — Security Sentinel (Hugo) patrol + lockdown."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture()
def sentinel_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import services.security_sentinel as ss

    monkeypatch.setattr(ss, "DATA", tmp_path)
    monkeypatch.setattr(ss, "AUTH_FAIL_FILE", tmp_path / "security_auth_failures.json")
    monkeypatch.setattr(ss, "LOCKDOWN_FILE", tmp_path / "security_lockdown.json")
    monkeypatch.setattr(ss, "LAST_PATROL_FILE", tmp_path / "security_patrol_last.json")
    return ss


def test_record_and_count_auth_failures(sentinel_tmp):
    ss = sentinel_tmp
    for _ in range(5):
        ss.record_auth_failure(kind="hub_key", client_ip="1.2.3.4")
    recent = ss._recent_auth_failures(minutes=60)
    assert len(recent) == 5


def test_lockdown_toggle(sentinel_tmp):
    ss = sentinel_tmp
    assert ss.is_lockdown_active() is False
    ss.set_lockdown(True, reason="test")
    assert ss.is_lockdown_active() is True
    ss.set_lockdown(False, reason="clear")
    assert ss.is_lockdown_active() is False


def test_patrol_detects_auth_burst_and_auto_lockdown(sentinel_tmp, monkeypatch):
    ss = sentinel_tmp
    for _ in range(ss._AUTH_BURST_THRESHOLD):
        ss.record_auth_failure(kind="hub_key", client_ip="9.9.9.9")

    class _S:
        environment = "development"
        hub_api_key = "x" * 32
        hub_ip_allowlist = ""
        telegram_webhook_secret = "sec"
        security_auto_lockdown = True

    monkeypatch.setattr(ss, "get_settings", lambda: _S())
    monkeypatch.setattr(ss, "_env_tracked_by_git", lambda: False)

    report = ss.run_patrol(notify=False, auto_lockdown=True)
    ids = {f["id"] for f in report["findings"]}
    assert "auth_burst" in ids
    assert report["lockdown"] is True
    assert "lockdown_enabled" in report["actions"]
    assert ss.LAST_PATROL_FILE.is_file()
    saved = json.loads(ss.LAST_PATROL_FILE.read_text(encoding="utf-8"))
    assert saved["lockdown"] is True


def test_client_ip_blocked_during_lockdown(sentinel_tmp, monkeypatch):
    ss = sentinel_tmp
    ss.set_lockdown(True, reason="unit")
    from services.hub_auth import client_ip_allowed

    assert client_ip_allowed("127.0.0.1") is True
    assert client_ip_allowed("8.8.8.8") is False


def test_get_system_prompt_security_sentinel():
    from config.agent_operating_spec import get_system_prompt

    prompt = get_system_prompt("security_sentinel")
    assert "Patrouiller" in prompt or "patrouille" in prompt.lower()
