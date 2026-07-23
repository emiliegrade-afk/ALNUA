"""Tests Obsidian vault read, bootstrap, and sync helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def sample_vault(tmp_path: Path) -> Path:
  """Minimal vault tree for unit tests."""
  lore = tmp_path / "wyrdheim" / "lore"
  gdd = tmp_path / "wyrdheim" / "gdd"
  lore.mkdir(parents=True)
  gdd.mkdir(parents=True)

  (lore / "LORE-WYR-001-test.md").write_text(
    """---
ref: LORE-WYR-001
project: wyrdheim
category: lieux
tags: [forêt, test]
---

# Forêt des Runes

Une forêt ancienne où les pierres murmurent.
""",
    encoding="utf-8",
  )

  (gdd / "GDD-WYR-biome-001.md").write_text(
    """---
ref: GDD-WYR-biome-001
---

# GDD Biome Test

## Vision
Biome sombre et brumeux.

## Mécaniques
Exploration libre.
""",
    encoding="utf-8",
  )
  return tmp_path


def test_parse_frontmatter_and_ref(sample_vault: Path) -> None:
  from services.obsidian_vault import read_note

  note = read_note(sample_vault / "wyrdheim" / "lore" / "LORE-WYR-001-test.md", vault=sample_vault)
  assert note.ref == "LORE-WYR-001"
  assert note.metadata["category"] == "lieux"
  assert note.metadata["tags"] == ["forêt", "test"]
  assert "Forêt des Runes" in note.title


def test_lore_note_to_entry(sample_vault: Path) -> None:
  from services.obsidian_vault import lore_note_to_entry, read_note

  note = read_note(sample_vault / "wyrdheim" / "lore" / "LORE-WYR-001-test.md", vault=sample_vault)
  entry = lore_note_to_entry(note)
  assert entry is not None
  assert entry["project"] == "wyrdheim"
  assert entry["category"] == "lieux"
  assert "murmurent" in entry["content"]


def test_bootstrap_vault_copies_templates(tmp_path: Path) -> None:
  from services.obsidian_vault import bootstrap_vault, get_canonical_vault_path

  target = tmp_path / "user_vault"
  result = bootstrap_vault(target)
  assert result["copied_count"] > 0
  assert (target / "_templates" / "APP-template.md").is_file()
  assert (target / "wyrdheim" / "lore").is_dir()
  assert get_canonical_vault_path().is_dir()


def test_sync_lore_dry_run(sample_vault: Path) -> None:
  from services.obsidian_sync import sync_lore_entries

  fake_db = MagicMock()
  result = sync_lore_entries(fake_db, vault=sample_vault, dry_run=True)
  assert result["synced"] == 1
  assert result["skipped"] == 0
  fake_db.table.assert_not_called()


def test_resolve_bootstrap_target_prefers_d(monkeypatch) -> None:
  from services import obsidian_vault as ov

  monkeypatch.setattr(ov.settings, "obsidian_vault_path", "")
  if ov._drive_root_exists(Path(r"D:\ObsidianVault")):
    target, reason = ov.resolve_bootstrap_target()
    assert target == Path(r"D:\ObsidianVault")
    assert reason == "default D:\\ObsidianVault"
  else:
    with pytest.raises(OSError, match="D:\\\\ is not available"):
      ov.resolve_bootstrap_target()


def test_resolve_bootstrap_target_c_fallback(monkeypatch) -> None:
  from services import obsidian_vault as ov

  monkeypatch.setattr(ov.settings, "obsidian_vault_path", "")
  if ov._drive_root_exists(Path(r"D:\ObsidianVault")):
    pytest.skip("D: present — C fallback not exercised")
  target, reason = ov.resolve_bootstrap_target(allow_c_fallback=True)
  assert target == ov.ROOT.parent / "ObsidianVault"
  assert "emergency" in reason


def test_resolve_bootstrap_target_explicit_missing_drive() -> None:
  from services.obsidian_vault import resolve_bootstrap_target

  with pytest.raises(OSError, match="Drive not available"):
    resolve_bootstrap_target(Path(r"Z:\ObsidianVault"))


def test_list_notes_excludes_templates(sample_vault: Path) -> None:
  from services.obsidian_vault import list_notes

  templates = sample_vault / "_templates"
  templates.mkdir()
  (templates / "LORE-WYR-template.md").write_text("# template", encoding="utf-8")

  notes = list_notes(vault=sample_vault, subdir="wyrdheim/lore")
  assert len(notes) == 1
  assert notes[0].ref == "LORE-WYR-001"
