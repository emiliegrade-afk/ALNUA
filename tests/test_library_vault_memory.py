"""Tests vault layout + library export + topic catalog (no live Obsidian required)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def vault_root(tmp_path, monkeypatch):
    vault = tmp_path / "ObsidianVault"
    vault.mkdir()
    monkeypatch.setattr(
        "services.obsidian_vault.get_vault_path",
        lambda: vault,
    )
    return vault


@pytest.fixture
def library_file(tmp_path, monkeypatch):
    path = tmp_path / "bureau_library.json"
    monkeypatch.setattr("services.bureau_library.LIBRARY_FILE", path)
    monkeypatch.setattr("services.library_vault_export.LIBRARY_FILE", path)
    return path


@pytest.fixture
def catalog_file(tmp_path, monkeypatch):
    path = tmp_path / "topic_catalog.json"
    monkeypatch.setattr("services.library_vault_export.CATALOG_FILE", path)
    monkeypatch.setattr("services.topic_catalog.CATALOG_FILE", path)
    return path


def test_ensure_vault_layout(vault_root: Path) -> None:
    from services.obsidian_vault import ensure_vault_layout

    result = ensure_vault_layout(vault_root)
    assert (vault_root / "library" / "app").is_dir()
    assert (vault_root / "library" / "_digests").is_dir()
    assert (vault_root / "memory" / "agents").is_dir()
    assert (vault_root / "library" / "_index" / "README.md").is_file()
    assert result["created_count"] > 0


def test_export_builds_catalog_and_notes(
    vault_root: Path,
    library_file: Path,
    catalog_file: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "services.team_enrichment.fanout_library_entry",
        lambda *a, **k: None,
    )

    from services.bureau_library import add_entry
    from services.library_vault_export import export_library_to_vault
    from services.topic_catalog import get_topic, list_topics

    add_entry(
        bureau="app",
        title="FastAPI streaming",
        summary="Streaming SSE utile pour chat agents.",
        digest="FastAPI helpers streaming pour agents Hub.",
        timing="now",
        topics=["FastAPI", "SSE"],
        agent_id="dev_app",
        query="FastAPI latest features 2026",
    )
    add_entry(
        bureau="app",
        title="Supabase Realtime",
        summary="Channels Realtime pour Naia.",
        timing="later",
        topics=["Supabase"],
        agent_id="dev_app",
    )

    result = export_library_to_vault(vault=vault_root, index_chroma=False)
    assert result["ok"]
    assert result["written"] == 2
    assert result["topic_count"] >= 2
    assert (vault_root / "library" / "_index" / "TOPICS.md").is_file()

    notes = list((vault_root / "library" / "app").glob("*.md"))
    assert notes
    text = notes[0].read_text(encoding="utf-8")
    assert "type: library" in text

    topics = list_topics(query="fastapi", limit=10)
    assert topics["total"] >= 1
    slug = topics["topics"][0]["slug"]
    detail = get_topic(slug)
    assert detail is not None
    assert detail["entries"]

    catalog = json.loads(catalog_file.read_text(encoding="utf-8"))
    assert catalog["entry_count"] == 2


def test_concat_digest_and_scan(
    vault_root: Path,
    catalog_file: Path,
    library_file: Path,
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        "services.team_enrichment.fanout_library_entry",
        lambda *a, **k: None,
    )
    from services.bureau_library import add_entry
    from services.library_vault_export import export_library_to_vault
    from skills.skill_library_memory import ensure_topic_digest, scan_library_topics

    add_entry(
        bureau="rd",
        title="Agent skills format",
        summary="SKILL.md packs",
        digest="Les Agent Skills isolent les competences dans SKILL.md.",
        timing="now",
        topics=["agent-skills"],
        agent_id="rnd_agent",
        query="agent skills",
    )
    export_library_to_vault(vault=vault_root)

    scanned = scan_library_topics("agent skills", bureau="rd", limit=5)
    assert scanned["total"] >= 1
    slug = scanned["topics"][0]["slug"]
    digest = ensure_topic_digest(slug, force=True)
    assert digest["ok"]
    assert (vault_root / digest["path"]).is_file()
