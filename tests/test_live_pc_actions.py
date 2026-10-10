"""Nadia Live Lot 5 — PC allowlist (DEC-039). Never launches a real process."""

from __future__ import annotations

from types import SimpleNamespace

from services import live_pc_actions as pc


def _cfg(**over):
    base = {
        "live_pc_actions_enabled": True,
        "live_pc_allowed_domains": "instagram.com,youtube.com,mail.google.com",
        "live_pc_allowed_apps": (
            "instagram=https://www.instagram.com,"
            "gmail=https://mail.google.com,"
            "youtube=https://www.youtube.com"
        ),
        "live_pc_allowed_dir": "",
    }
    base.update(over)
    return SimpleNamespace(**base)


def test_maybe_open_ignores_chat(monkeypatch):
    monkeypatch.setattr(pc, "get_settings", lambda: _cfg())
    assert pc.maybe_open("Quelle est la météo à Paris ?") is None
    assert pc.maybe_open("lance une recherche R&D robotique") is None
    assert pc.wants_open("va sur Instagram") is True


def test_disabled_flag_is_honest(monkeypatch):
    monkeypatch.setattr(pc, "get_settings", lambda: _cfg(live_pc_actions_enabled=False))
    out = pc.run_open("ouvre Instagram")
    assert "LIVE_PC_ACTIONS_ENABLED" in out


def test_va_sur_opens_named_page(monkeypatch):
    launched: list[str] = []
    monkeypatch.setattr(pc, "get_settings", lambda: _cfg())
    monkeypatch.setattr(pc, "_launch_url", launched.append)
    out = pc.run_open("va sur Instagram")
    assert launched == ["https://www.instagram.com/"]
    assert "instagram.com" in out


def test_named_key_opens_https(monkeypatch):
    launched: list[str] = []
    monkeypatch.setattr(pc, "get_settings", lambda: _cfg())
    monkeypatch.setattr(pc, "_launch_url", launched.append)
    out = pc.run_open("ouvre-moi Instagram")
    assert launched == ["https://www.instagram.com/"]
    assert "instagram.com" in out


def test_https_on_allowlist(monkeypatch):
    launched: list[str] = []
    monkeypatch.setattr(pc, "get_settings", lambda: _cfg())
    monkeypatch.setattr(pc, "_launch_url", launched.append)
    out = pc.run_open("ouvre https://www.youtube.com/watch?v=abc")
    assert launched[0].startswith("https://www.youtube.com/")
    assert "youtube.com" in out


def test_http_and_unknown_domain_are_refused(monkeypatch):
    launched: list[str] = []
    monkeypatch.setattr(pc, "get_settings", lambda: _cfg())
    monkeypatch.setattr(pc, "_launch_url", launched.append)
    assert pc.parse_open("ouvre http://instagram.com", _cfg()) is None
    assert pc.parse_open("ouvre https://evil.example", _cfg()) is None
    assert launched == []
    msg = pc.run_open("ouvre https://evil.example")
    assert "liste blanche" in msg.lower() or "pages" in msg.lower()


def test_suffix_does_not_match_lookalike():
    cfg = _cfg()
    assert pc.parse_open("ouvre https://notinstagram.com", cfg) is None
    assert pc.parse_open("ouvre https://www.instagram.com/alnua", cfg) is not None
