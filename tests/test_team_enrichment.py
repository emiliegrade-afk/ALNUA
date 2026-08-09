"""Phase 3 — team enrichment from bureau library."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from services.team_enrichment import (
    agents_for_bureau,
    enrich_team_from_library,
    fanout_library_entry,
)


def test_agents_for_bureau_app() -> None:
    agents = agents_for_bureau("app")
    assert "dev_app" in agents
    assert "dev_backend" in agents


def test_fanout_library_entry_calls_mem0(monkeypatch: pytest.MonkeyPatch) -> None:
    remembered: list[tuple[str, str]] = []

    def fake_remember(text: str, *, agent_id: str) -> None:
        remembered.append((agent_id, text))

    monkeypatch.setattr("skills.skill_mem0.remember", fake_remember)
    monkeypatch.setattr(
        "services.library_distribution.record_distributed",
        lambda *_a, **_k: None,
    )
    with patch("services.team_enrichment.distill_library_entry_for_agent"):
        agents = fanout_library_entry(
            {
                "id": "test-entry",
                "bureau": "app",
                "title": "Expo SDK 54",
                "summary": "Nouveautés navigation.",
                "timing": "now",
            }
        )
    assert "dev_app" in agents
    assert len(remembered) >= 2
    assert "Expo SDK 54" in remembered[0][1]
    assert "library:test-entry" in remembered[0][1]


def test_enrich_team_empty_library(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "bureau_library.json"
    path.write_text('{"version":1,"entries":[],"reports":[]}', encoding="utf-8")
    monkeypatch.setattr("services.bureau_library.LIBRARY_FILE", path)
    result = enrich_team_from_library()
    assert result["entries_processed"] == 0
    assert result["agents_enriched"] == 0


def test_get_library_context_injects_bureau(monkeypatch: pytest.MonkeyPatch) -> None:
    from skills.skill_agent_learning import get_library_context

    monkeypatch.setattr(
        "services.topic_catalog.search_topics_for_task",
        lambda *_a, **_k: [],
    )
    monkeypatch.setattr(
        "services.bureau_library.list_entries",
        lambda **kwargs: {
            "entries": [
                {
                    "timing": "now",
                    "title": "Test IA",
                    "summary": "Résumé test",
                    "topics": ["ia"],
                }
            ]
        },
    )
    monkeypatch.setattr("services.bureau_library.bureau_for_agent", lambda _aid: "rd")
    block = get_library_context("rnd_agent", "recherche")
    assert "BIBLIOTHÈQUE" in block
    assert "Test IA" in block
