"""Phase 3 tests — GDD manager chunking and API gates."""

from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-supabase-key")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")
os.environ.setdefault("HUB_API_KEY", "test-hub-key-for-ci")
os.environ.setdefault("ENVIRONMENT", "development")

HUB_HEADERS = {"X-Hub-Key": "test-hub-key-for-ci"}

SAMPLE_GDD = """# Wyrdheim GDD

## Monde
Le continent de Wyrdheim est divisé en trois royaumes.

## Combat
Les combats sont au tour par tour avec des dés de mana.
"""


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from config.settings import get_settings

    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    get_settings.cache_clear()
    monkeypatch.setattr("database.supabase_client.get_supabase", lambda: MagicMock())
    from api.app import app

    return TestClient(app)


def test_chunk_gdd_markdown_sections() -> None:
    from services.gdd_manager import chunk_gdd_markdown, parse_markdown_sections

    sections = parse_markdown_sections(SAMPLE_GDD)
    titles = [t for t, _ in sections]
    assert "Monde" in titles
    assert "Combat" in titles

    drafts = chunk_gdd_markdown(SAMPLE_GDD)
    assert len(drafts) >= 2
    assert all(d.token_estimate > 0 for d in drafts)


def test_gdd_endpoints_disabled_when_flag_off(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from config.settings import get_settings

    monkeypatch.setenv("GDD_MANAGER_ENABLED", "0")
    get_settings.cache_clear()

    res = client.get("/gdd/proj-1/sections", headers=HUB_HEADERS)
    assert res.status_code == 404


def test_gdd_ingest_markdown(monkeypatch: pytest.MonkeyPatch) -> None:
    from config.settings import get_settings

    monkeypatch.setenv("GDD_MANAGER_ENABLED", "1")
    get_settings.cache_clear()

    fake_db = MagicMock()
    fake_db.select.return_value = [{"id": "p1", "branch": "gaming", "name": "Wyrdheim"}]
    fake_db.insert_many.side_effect = lambda _t, rows: [{"id": f"c{i}"} for i in range(len(rows))]
    fake_db.table.return_value.delete.return_value.eq.return_value.execute.return_value = None

    from services.gdd_manager import ingest_gdd

    result = ingest_gdd(
        fake_db,
        project_id="p1",
        markdown=SAMPLE_GDD,
        document_title="Wyrdheim GDD",
    )

    assert result["chunks_count"] >= 2
    assert "Monde" in result["sections"]
    fake_db.insert_many.assert_called_once()
    inserted_rows = fake_db.insert_many.call_args[0][1]
    assert len(inserted_rows) == result["chunks_count"]


def test_gdd_search_client_filter() -> None:
    fake_db = MagicMock()
    fake_db.table.return_value.select.return_value.eq.return_value.ilike.return_value.limit.return_value.execute.side_effect = Exception(
        "no ilike"
    )
    fake_db.select.return_value = [
        {
            "id": "1",
            "section_title": "Combat",
            "chunk_index": 0,
            "content": "mana et dés de combat",
            "token_estimate": 10,
            "document_title": "GDD",
        },
        {
            "id": "2",
            "section_title": "Monde",
            "chunk_index": 0,
            "content": "royaumes lointains",
            "token_estimate": 8,
            "document_title": "GDD",
        },
    ]

    from services.gdd_manager import search_gdd_chunks

    hits = search_gdd_chunks(fake_db, "p1", "mana")
    assert len(hits) == 1
    assert hits[0]["section_title"] == "Combat"


def test_gdd_ingest_rejects_non_gaming_project() -> None:
    fake_db = MagicMock()
    fake_db.select.return_value = [{"id": "p1", "branch": "app", "name": "Hub"}]

    from services.gdd_manager import ingest_gdd

    with pytest.raises(ValueError, match="gaming"):
        ingest_gdd(fake_db, project_id="p1", markdown=SAMPLE_GDD)


def test_admin_flags_includes_gdd(client: TestClient) -> None:
    res = client.get("/admin/flags", headers=HUB_HEADERS)
    assert res.status_code == 200
    assert "gdd_manager_enabled" in res.json()
