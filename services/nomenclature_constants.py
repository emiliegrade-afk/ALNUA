"""ALNUA reference ID types, patterns, and shared constants."""

from __future__ import annotations

import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

ROOT = Path(__file__).resolve().parent.parent
COUNTERS_FILE = ROOT / "data" / "nomenclature_counters.json"

RefKind = Literal[
    "APP",
    "GDD",
    "LORE",
    "ASSET",
    "BUG",
    "COLLAB",
    "RND",
]

SCOPE_WYR = "WYR"
SCOPE_NWA = "NWA"

_ASSET_SUBTYPES = frozenset({"ENV", "CHAR", "VFX", "MAT", "SFX", "APP"})

# APP-naia-001 | APP-naia-F003 | GDD-WYR-biome-001 | LORE-WYR-001 | LORE-NWA-012
# ASSET-WYR-ENV-001 | ASSET-APP-naia-001 | BUG-20260624-001 | COLLAB-partner-001 | RND-diffusion-001
REF_PATTERNS: dict[str, re.Pattern[str]] = {
    "APP": re.compile(
        r"^APP-(?P<slug>[a-z0-9-]+)-(?:(?:F(?P<fseq>\d{3}))|(?P<seq>\d{3}))$",
        re.I,
    ),
    "GDD": re.compile(
        r"^GDD-(?P<scope>WYR|NWA)-(?P<slug>[a-z0-9-]+)-(?P<seq>\d{3})$", re.I
    ),
    "LORE": re.compile(r"^LORE-(?P<scope>WYR|NWA)-(?P<seq>\d{3})$", re.I),
    "ASSET": re.compile(
        r"^ASSET-(?:(?P<scope>WYR)-(?P<subtype>ENV|CHAR|VFX|MAT|SFX)|APP-(?P<app_slug>[a-z0-9-]+))-(?P<seq>\d{3})$",
        re.I,
    ),
    "BUG": re.compile(r"^BUG-(?P<day>\d{8})-(?P<seq>\d{3})$", re.I),
    "COLLAB": re.compile(r"^COLLAB-(?P<slug>[a-z0-9-]+)-(?P<seq>\d{3})$", re.I),
    "RND": re.compile(r"^RND-(?P<slug>[a-z0-9-]+)-(?P<seq>\d{3})$", re.I),
}

_lock = threading.Lock()


@dataclass(frozen=True)
class ParsedRef:
    raw: str
    kind: RefKind
    scope: str | None = None
    slug: str | None = None
    subtype: str | None = None
    day: str | None = None
    seq: int = 0
    counter_key: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "raw": self.raw,
            "kind": self.kind,
            "scope": self.scope,
            "slug": self.slug,
            "subtype": self.subtype,
            "day": self.day,
            "seq": self.seq,
            "counter_key": self.counter_key,
        }
