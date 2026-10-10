"""DEC-044 — screen pick + confirmed click/type. Never moves a real window in tests."""

from __future__ import annotations

from types import SimpleNamespace

from services import live_pc_actions as pc
from services import live_pc_display as disp
from services import live_pc_input as inp


def _cfg(**over):
    base = {
        "live_pc_actions_enabled": True,
        "live_pc_allowed_domains": "instagram.com,youtube.com,mail.google.com",
        "live_pc_allowed_apps": (
            "instagram=https://www.instagram.com,"
            "gmail=https://mail.google.com,"
            "discord=https://discord.com/app"
        ),
        "live_pc_allowed_dir": "",
    }
    base.update(over)
    return SimpleNamespace(**base)


def test_parse_screen_number_and_sides(monkeypatch):
    monkeypatch.setattr(
        disp,
        "list_displays",
        lambda: [
            disp.Display(1, 0, 0, 1920, 1080),
            disp.Display(2, 1920, 0, 3840, 1080),
        ],
    )
    assert disp.parse_screen("ouvre Instagram sur l'écran 2") == 2
    assert disp.parse_screen("à droite") == 2
    assert disp.parse_screen("à gauche") == 1
    assert disp.parse_screen("ouvre Instagram") is None


def test_open_moves_to_named_screen(monkeypatch):
    launched: list[str] = []
    placed: list[tuple[int, str]] = []
    monkeypatch.setattr(pc, "get_settings", lambda: _cfg())
    monkeypatch.setattr(pc, "_launch_url", launched.append)
    monkeypatch.setattr(
        "services.live_pc_display.wait_then_place",
        lambda idx, hint, delay=1.2: placed.append((idx, hint)) or "ok",
    )
    out = pc.run_open("ouvre Instagram sur l'écran 2")
    assert launched
    assert placed == [(2, "instagram")]
    assert "instagram" in out.lower()


def test_type_is_draft_not_executed(monkeypatch):
    inp.reset_for_tests()
    monkeypatch.setattr(inp, "get_settings", lambda: _cfg())
    typed: list[tuple[int, str]] = []
    monkeypatch.setattr(inp, "_type_into", lambda hwnd, text: typed.append((hwnd, text)))
    monkeypatch.setattr(inp, "find_window", lambda hint: 0)
    out = inp.propose_input("tape bonjour dans Discord")
    assert "```draft" in out
    assert "pc_input" in out
    assert typed == []
    draft_id = inp.latest_input_id()
    assert draft_id
    result = inp.execute_input(draft_id)
    assert result["success"] is False
    assert "introuvable" in result["message"].lower()


def test_type_executes_only_after_confirm(monkeypatch):
    inp.reset_for_tests()
    monkeypatch.setattr(inp, "get_settings", lambda: _cfg())
    typed: list[str] = []
    monkeypatch.setattr(inp, "find_window", lambda hint: 42)
    monkeypatch.setattr(inp, "_type_into", lambda hwnd, text: typed.append(text))
    inp.propose_input("tape « hello ALNUA » dans Discord")
    out = inp.execute_input(inp.latest_input_id() or "")
    assert out["success"] is True
    assert typed == ["hello ALNUA"]


def test_refuses_unknown_window():
    assert inp.parse_input("tape secret dans notepad") is None
    assert inp.wants_pc_input("cherche les actualités") is False
    assert inp.wants_pc_input("clique au centre sur Gmail") is True
