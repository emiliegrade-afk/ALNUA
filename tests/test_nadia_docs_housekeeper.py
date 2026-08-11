"""Tests — Nadia docs + PC housekeeper (quarantine model)."""

from __future__ import annotations

from pathlib import Path

import services.nadia_docs as nadia_docs
import services.pc_housekeeper_actions as hk_actions
import services.pc_housekeeper_core as hk_core
from config.contract_templates_registry import template_prompt_block
from config.agent_operating_spec import get_system_prompt


def test_nadia_docs_create_read_update(tmp_path, monkeypatch):
    monkeypatch.setattr(nadia_docs, "DOCS_DIR", tmp_path)
    monkeypatch.setattr(nadia_docs, "INDEX_FILE", tmp_path / "index.json")
    monkeypatch.setattr(nadia_docs, "ROOT", tmp_path.parent)

    entry = nadia_docs.create_document("Test Note", "# Hello\n\nWorld", doc_type="note")
    assert entry["id"]
    doc = nadia_docs.read_document(entry["id"])
    assert doc is not None
    assert "Hello" in (doc.get("content") or "")
    updated = nadia_docs.update_document(entry["id"], "# Updated\n", title="Renamed")
    assert updated is not None
    assert updated["title"] == "Renamed"
    assert list(nadia_docs.list_documents())


def test_housekeeper_propose_and_quarantine(tmp_path, monkeypatch):
    desk = tmp_path / "Desktop"
    desk.mkdir()
    clutter = desk / "photo.jpg"
    clutter.write_bytes(b"fake")
    data = tmp_path / "data"
    data.mkdir()
    monkeypatch.setattr(hk_core, "DATA", data)
    monkeypatch.setattr(hk_core, "STATE_FILE", data / "housekeeper_state.json")
    monkeypatch.setattr(hk_core, "REPORT_DIR", data / "housekeeper_reports")
    monkeypatch.setattr(hk_core, "DEFAULT_QUARANTINE", data / "housekeeper_quarantine")
    monkeypatch.setattr(hk_core, "DEFAULT_PROPOSALS", data / "housekeeper_proposals")
    monkeypatch.setattr(hk_actions, "DEFAULT_QUARANTINE", data / "housekeeper_quarantine")
    monkeypatch.setattr(hk_actions, "DEFAULT_PROPOSALS", data / "housekeeper_proposals")
    monkeypatch.setattr(hk_actions, "REPORT_DIR", data / "housekeeper_reports")
    # pytest tmp lives under AppData on Windows — bypass for unit test
    monkeypatch.setattr(hk_core, "_is_blocked", lambda _p: False)
    monkeypatch.setattr(hk_actions, "_is_blocked", lambda _p: False)

    scan = hk_core.scan_clutter([desk])
    assert scan["count"] >= 1
    prop = hk_core.propose_organization(scan)
    assert prop["proposals"]
    q = hk_actions.quarantine_for_delete([str(clutter)])
    assert q["moved"]
    assert not clutter.exists()
    assert Path(q["moved"][0]["quarantine"]).is_file()
    purged = hk_actions.purge_quarantine(confirm=False)
    assert purged["ok"] is False
    purged2 = hk_actions.purge_quarantine(confirm=True)
    assert purged2["ok"] is True


def test_template_body_injected():
    block = template_prompt_block("nda")
    assert "Informations Confidentielles" in block or "confidentiel" in block.lower()
    assert "Solène" in block or "avocat" in block.lower()


def test_housekeeper_system_prompt():
    prompt = get_system_prompt("housekeeper")
    assert "quarantaine" in prompt.lower() or "range" in prompt.lower()
