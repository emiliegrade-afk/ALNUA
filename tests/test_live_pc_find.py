"""Nadia Live — find a folder/file in user-profile roots only."""

from __future__ import annotations

from types import SimpleNamespace

from services import live_pc_find as find


def _cfg(**over):
    base = {"live_pc_actions_enabled": True, "live_pc_allowed_dir": ""}
    base.update(over)
    return SimpleNamespace(**base)


def test_wants_find_not_web_or_instagram():
    assert find.wants_find("cherche les actualités IA") is False
    assert find.wants_find("ouvre Instagram") is False
    assert find.wants_find("lance une recherche R&D robotique") is False
    assert find.wants_find("cherche le dossier factures") is True
    assert find.wants_find("ouvre le dossier ALNUA") is True
    assert find.wants_find("trouve contrat sur mon PC") is True


def test_extract_rejects_path_escape():
    assert find.extract_find_query("cherche le dossier ..\\Windows") == ""
    assert find.extract_find_query("cherche le dossier factures") == "factures"


def test_search_and_open_unique_folder(tmp_path, monkeypatch):
    desk = tmp_path / "Desktop"
    docs = tmp_path / "Documents"
    down = tmp_path / "Downloads"
    target = desk / "Factures_2026"
    target.mkdir(parents=True)
    docs.mkdir()
    (docs / "notes.txt").write_text("x", encoding="utf-8")
    down.mkdir()
    opened: list[str] = []
    monkeypatch.setattr(find, "get_settings", lambda: _cfg())
    monkeypatch.setattr(find, "_reveal", lambda p: opened.append(str(p)))
    out = find.run_find(
        "ouvre le dossier Factures_2026",
        roots=[desk, docs, down],
    )
    assert "Factures_2026" in out
    assert "```list" in out
    assert opened and opened[0].endswith("Factures_2026")


def test_refuses_exe_open(tmp_path, monkeypatch):
    desk = tmp_path / "Desktop"
    desk.mkdir()
    (desk / "setup.exe").write_bytes(b"x")
    opened: list[str] = []
    monkeypatch.setattr(find, "get_settings", lambda: _cfg())
    monkeypatch.setattr(find, "_reveal", lambda p: opened.append(str(p)))
    out = find.run_find("ouvre le fichier setup", roots=[desk])
    assert "setup.exe" in out
    assert opened == []


def test_disabled_flag(monkeypatch):
    monkeypatch.setattr(find, "get_settings", lambda: _cfg(live_pc_actions_enabled=False))
    out = find.run_find("cherche le dossier factures")
    assert "LIVE_PC_ACTIONS_ENABLED" in out


def test_detect_find_wins_over_open():
    from services.secretary_intents_detect import detect_find_pc, detect_open_pc

    assert detect_find_pc("ouvre le dossier factures") is True
    assert detect_open_pc("ouvre le dossier factures") is False
    assert detect_open_pc("ouvre Instagram") is True
