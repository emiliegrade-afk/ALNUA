"""Persisted counter store and ref formatting for ALNUA nomenclature."""

from __future__ import annotations

import json
import logging
import re
from datetime import date
from pathlib import Path
from typing import Any

from services.nomenclature_constants import SCOPE_WYR, RefKind

logger = logging.getLogger(__name__)


def _counters_file() -> Path:
    """Resolve at runtime so tests can monkeypatch ``services.nomenclature.COUNTERS_FILE``."""
    import services.nomenclature as nom_mod

    return nom_mod.COUNTERS_FILE


def _slugify(value: str) -> str:
    s = value.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")[:48] or "item"


def _load_store() -> dict[str, Any]:
    counters_file = _counters_file()
    if not counters_file.exists():
        return {"counters": {}, "issued": []}
    try:
        data = json.loads(counters_file.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("counters", {})
            data.setdefault("issued", [])
            return data
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("nomenclature store corrupt, resetting: %s", exc)
    return {"counters": {}, "issued": []}


def _save_store(data: dict[str, Any]) -> None:
    counters_file = _counters_file()
    counters_file.parent.mkdir(parents=True, exist_ok=True)
    counters_file.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _counter_key_for(
    kind: RefKind,
    *,
    scope: str | None = None,
    slug: str | None = None,
    subtype: str | None = None,
    day: str | None = None,
    feature: bool = False,
) -> str:
    slug_n = _slugify(slug) if slug else ""
    if kind == "LORE":
        return f"LORE-{(scope or SCOPE_WYR).upper()}"
    if kind == "GDD":
        return f"GDD-{(scope or SCOPE_WYR).upper()}-{slug_n}"
    if kind == "APP":
        return f"APP-{slug_n}{'-F' if feature else ''}"
    if kind == "ASSET":
        if subtype and subtype.upper() == "APP":
            return f"ASSET-APP-{_slugify(slug or 'app')}"
        if slug and not scope:
            return f"ASSET-APP-{_slugify(slug)}"
        return f"ASSET-{(scope or SCOPE_WYR).upper()}-{(subtype or 'ENV').upper()}"
    if kind == "BUG":
        return f"BUG-{day or date.today().strftime('%Y%m%d')}"
    if kind == "COLLAB":
        return f"COLLAB-{slug_n}"
    if kind == "RND":
        return f"RND-{slug_n}"
    raise ValueError(f"Unknown kind: {kind}")


def _format_ref(
    kind: RefKind,
    seq: int,
    *,
    scope: str | None = None,
    slug: str | None = None,
    subtype: str | None = None,
    day: str | None = None,
    feature: bool = False,
) -> str:
    n = f"{seq:03d}"
    if kind == "LORE":
        return f"LORE-{(scope or SCOPE_WYR).upper()}-{n}"
    if kind == "GDD":
        return f"GDD-{(scope or SCOPE_WYR).upper()}-{_slugify(slug or 'doc')}-{n}"
    if kind == "APP":
        mid = f"{_slugify(slug or 'app')}-F{n}" if feature else f"{_slugify(slug or 'app')}-{n}"
        return f"APP-{mid}"
    if kind == "ASSET":
        if subtype and subtype.upper() == "APP":
            return f"ASSET-APP-{_slugify(slug or 'app')}-{n}"
        return f"ASSET-{(scope or SCOPE_WYR).upper()}-{(subtype or 'ENV').upper()}-{n}"
    if kind == "BUG":
        return f"BUG-{day or date.today().strftime('%Y%m%d')}-{n}"
    if kind == "COLLAB":
        return f"COLLAB-{_slugify(slug or 'partner')}-{n}"
    if kind == "RND":
        return f"RND-{_slugify(slug or 'topic')}-{n}"
    raise ValueError(f"Unknown kind: {kind}")


def _bump_counter(store: dict[str, Any], key: str, minimum: int = 0) -> int:
    counters: dict[str, int] = store["counters"]
    current = int(counters.get(key, 0))
    next_val = max(current, minimum) + 1
    counters[key] = next_val
    return next_val
