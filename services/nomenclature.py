"""
nomenclature.py — ALNUA reference IDs (APP-, LORE-WYR-, GDD-, BUG-, etc.).

Counters persist in ``data/nomenclature_counters.json``. Vault scan reconciles
sequence numbers so Obsidian and Hub stay aligned.
"""

from __future__ import annotations

from services.nomenclature_constants import (  # noqa: F401 — re-export
    COUNTERS_FILE,
    REF_PATTERNS,
    ROOT,
    SCOPE_NWA,
    SCOPE_WYR,
    ParsedRef,
    RefKind,
)
from services.nomenclature_ops import (  # noqa: F401 — re-export
    next_ref,
    peek_next_ref,
    reconcile_refs,
)
from services.nomenclature_parse import parse_ref, validate_ref  # noqa: F401 — re-export
from services.nomenclature_store import _load_store  # noqa: F401 — re-export
from services.nomenclature_vault import (  # noqa: F401 — re-export
    create_obsidian_stub,
    reconcile_vault,
    suggest_obsidian_path,
)

__all__ = [
    "COUNTERS_FILE",
    "ParsedRef",
    "REF_PATTERNS",
    "ROOT",
    "SCOPE_NWA",
    "SCOPE_WYR",
    "RefKind",
    "_load_store",
    "create_obsidian_stub",
    "next_ref",
    "parse_ref",
    "peek_next_ref",
    "reconcile_refs",
    "reconcile_vault",
    "suggest_obsidian_path",
    "validate_ref",
]
