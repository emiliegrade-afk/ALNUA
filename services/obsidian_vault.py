"""
obsidian_vault.py — Read and parse the local Obsidian vault (filesystem).

Vault canonical copy lives in ``vault/obsidian/``; runtime path from OBSIDIAN_VAULT_PATH.
"""

from __future__ import annotations

from config.settings import settings

from services.obsidian_vault_constants import (
    CANONICAL_VAULT,
    LORE_CATEGORIES,
    LORE_PROJECTS,
    ROOT,
    SKIP_DIRS,
    VAULT_LAYOUT_DIRS,
    VaultNote,
)
from services.obsidian_vault_lore import bootstrap_vault, lore_note_to_entry
from services.obsidian_vault_path import (
    _drive_root_exists,
    ensure_vault_layout,
    get_canonical_vault_path,
    get_vault_path,
    resolve_bootstrap_target,
)
from services.obsidian_vault_read import (
    find_notes_by_ref_prefix,
    iter_markdown_files,
    list_notes,
    read_note,
)

__all__ = [
    "CANONICAL_VAULT",
    "LORE_CATEGORIES",
    "LORE_PROJECTS",
    "ROOT",
    "SKIP_DIRS",
    "VAULT_LAYOUT_DIRS",
    "VaultNote",
    "_drive_root_exists",
    "bootstrap_vault",
    "ensure_vault_layout",
    "find_notes_by_ref_prefix",
    "get_canonical_vault_path",
    "get_vault_path",
    "iter_markdown_files",
    "list_notes",
    "lore_note_to_entry",
    "read_note",
    "resolve_bootstrap_target",
    "settings",
]
