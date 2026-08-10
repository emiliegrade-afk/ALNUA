"""Obsidian vault — constants and VaultNote model."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
CANONICAL_VAULT = ROOT / "vault" / "obsidian"

SKIP_DIRS = {".obsidian", ".trash", ".git", "__pycache__"}
LORE_CATEGORIES = frozenset(
    {"factions", "personnages", "lieux", "histoire", "magie", "economie", "quetes"}
)
LORE_PROJECTS = frozenset({"wyrdheim", "naia_world", "shared"})

VAULT_LAYOUT_DIRS: tuple[str, ...] = (
    "wyrdheim/lore",
    "wyrdheim/gdd",
    "wyrdheim/biomes",
    "wyrdheim/creatures",
    "apps",
    "rnd",
    "collabs",
    "daily",
    "library",
    "library/_index",
    "library/_digests",
    "library/hub",
    "library/secretary",
    "library/app",
    "library/gaming",
    "library/robo",
    "library/marketing",
    "library/rd",
    "library/finances",
    "library/analytics",
    "library/academy",
    "memory",
    "memory/agents",
)


@dataclass
class VaultNote:
    """One markdown note relative to vault root."""

    rel_path: str
    title: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def ref(self) -> str | None:
        ref = self.metadata.get("ref")
        if ref:
            return str(ref).strip()
        match = re.search(
            r"^(?:ref:\s*)?((?:APP|GDD|LORE|BUG|COLLAB|RND|ASSET)-[\w-]+)",
            self.content,
            re.MULTILINE | re.IGNORECASE,
        )
        return match.group(1) if match else None
