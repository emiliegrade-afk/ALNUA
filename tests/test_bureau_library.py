"""Tests bureau library — store, list, nothing discarded."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def library_file(tmp_path, monkeypatch):
    path = tmp_path / "bureau_library.json"
    monkeypatch.setattr("services.bureau_library.LIBRARY_FILE", path)
    return path


def test_add_and_list_entry(library_file: Path) -> None:
    from services.bureau_library import add_entry, list_entries

    add_entry(
        bureau="app",
        title="Expo SDK 52",
        summary="Nouvelles APIs — utile pour Théo plus tard.",
        timing="later",
        agent_id="dev_app",
    )
    add_entry(
        bureau="rd",
        title="Agents multi-LLM",
        summary="Pattern orchestration — applicable au Hub.",
        timing="now",
        agent_id="rnd_agent",
    )

    all_entries = list_entries(limit=10)
    assert all_entries["total"] == 2
    assert all_entries["counts_by_timing"]["later"] == 1
    assert all_entries["counts_by_timing"]["now"] == 1

    app_only = list_entries(bureau="app")
    assert app_only["total"] == 1
    assert app_only["entries"][0]["title"] == "Expo SDK 52"

    data = json.loads(library_file.read_text(encoding="utf-8"))
    assert len(data["entries"]) == 2
