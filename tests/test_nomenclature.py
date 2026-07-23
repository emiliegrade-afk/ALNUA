"""Tests ALNUA nomenclature ref IDs."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def counters_file(tmp_path: Path, monkeypatch):
    path = tmp_path / "nomenclature_counters.json"
    monkeypatch.setattr("services.nomenclature.COUNTERS_FILE", path)
    return path


def test_parse_lore_and_gdd() -> None:
    from services.nomenclature import parse_ref

    lore = parse_ref("LORE-WYR-042")
    assert lore is not None
    assert lore.kind == "LORE"
    assert lore.seq == 42
    assert lore.counter_key == "LORE-WYR"

    gdd = parse_ref("GDD-WYR-biome-sombre-001")
    assert gdd is not None
    assert gdd.slug == "biome-sombre"


def test_parse_app_feature() -> None:
    from services.nomenclature import parse_ref

    app = parse_ref("APP-naia-F003")
    assert app is not None
    assert app.kind == "APP"
    assert app.seq == 3
    assert "F" in app.counter_key


def test_next_ref_increments(counters_file: Path) -> None:
    from services.nomenclature import next_ref, peek_next_ref

    assert peek_next_ref("LORE", scope="WYR") == "LORE-WYR-001"
    r1 = next_ref("LORE", scope="WYR")
    r2 = next_ref("LORE", scope="WYR")
    assert r1 == "LORE-WYR-001"
    assert r2 == "LORE-WYR-002"


def test_reconcile_refs_updates_counters(counters_file: Path) -> None:
    from services.nomenclature import next_ref, reconcile_refs

    next_ref("LORE", scope="WYR")
    out = reconcile_refs(["LORE-WYR-010", "LORE-WYR-005", "INVALID"])
    assert out["parsed"] == 2
    assert "INVALID" in out["invalid"]
    assert out["counters"]["LORE-WYR"] == 10


def test_create_obsidian_stub(tmp_path: Path) -> None:
    from services.nomenclature import create_obsidian_stub
    from services.obsidian_vault import bootstrap_vault

    vault = tmp_path / "vault"
    bootstrap_vault(vault)

    ref = "LORE-WYR-001"
    result = create_obsidian_stub(ref, vault=vault, title="Test Lore")
    assert result["created"] is True
    path = vault / "wyrdheim" / "lore" / "LORE-WYR-001.md"
    assert path.is_file()
    assert "ref: LORE-WYR-001" in path.read_text(encoding="utf-8")
