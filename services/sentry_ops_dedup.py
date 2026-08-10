"""Dedup store for Sentry ingest fingerprints."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _dedup_path() -> Path:
    from services.sentry_ops import _DEDUP_PATH

    return _DEDUP_PATH


def load_dedup() -> dict[str, Any]:
    path = _dedup_path()
    if not path.exists():
        return {"fingerprints": {}, "recent": []}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"fingerprints": {}, "recent": []}


def save_dedup(data: dict[str, Any]) -> None:
    path = _dedup_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
