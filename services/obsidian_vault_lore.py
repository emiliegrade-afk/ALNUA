"""Obsidian vault — lore mapping and canonical bootstrap."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.obsidian_vault_constants import (
    CANONICAL_VAULT,
    LORE_CATEGORIES,
    LORE_PROJECTS,
    VaultNote,
)
from services.obsidian_vault_path import ensure_vault_layout, get_vault_path


def lore_note_to_entry(note: VaultNote) -> dict[str, Any] | None:
    """
    Map a vault lore note to a ``lore_entries`` row payload.
    Returns None if the note is not a lore document.
    """
    ref = (note.ref or "").upper()
    if not ref.startswith("LORE-"):
        return None

    project = str(note.metadata.get("project", "wyrdheim")).strip().lower()
    if project not in LORE_PROJECTS:
        if "NWA" in ref:
            project = "naia_world"
        else:
            project = "wyrdheim"

    category = str(note.metadata.get("category", "histoire")).strip().lower()
    if category not in LORE_CATEGORIES:
        category = "histoire"

    tags = note.metadata.get("tags", [])
    if isinstance(tags, str):
        tags = [t.strip() for t in tags.split(",") if t.strip()]

    content = note.content.strip()
    if not content:
        return None

    return {
        "title": note.title[:500],
        "category": category,
        "project": project,
        "content": content[:50_000],
        "tags": tags,
        "_vault_path": note.rel_path,
        "_ref": ref,
    }


def bootstrap_vault(target: Path | None = None, *, force: bool = False) -> dict[str, Any]:
    """
    Copy canonical ``vault/obsidian`` tree into the user vault.
    Skips existing files unless ``force=True``.
    """
    dest = target or get_vault_path()
    dest.mkdir(parents=True, exist_ok=True)

    copied: list[str] = []
    skipped: list[str] = []

    for src in CANONICAL_VAULT.rglob("*"):
        if src.is_dir():
            continue
        rel = src.relative_to(CANONICAL_VAULT)
        out = dest / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists() and not force:
            skipped.append(str(rel).replace("\\", "/"))
            continue
        out.write_bytes(src.read_bytes())
        copied.append(str(rel).replace("\\", "/"))

    layout = ensure_vault_layout(dest)

    return {
        "target": str(dest),
        "copied": copied,
        "skipped": skipped,
        "copied_count": len(copied),
        "skipped_count": len(skipped),
        "layout": layout,
    }
