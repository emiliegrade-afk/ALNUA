"""JSON persistence for bureau library."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any

from pathlib import Path

logger = logging.getLogger(__name__)


def _library_path() -> Path:
    """Resolve LIBRARY_FILE via façade so tests can monkeypatch one path."""
    from services.bureau_library import LIBRARY_FILE

    return LIBRARY_FILE


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_store() -> dict[str, Any]:
    return {"version": 1, "entries": [], "reports": [], "archives": []}


def _load_store() -> dict[str, Any]:
    library_file = _library_path()
    if not library_file.exists():
        return _empty_store()
    try:
        data = json.loads(library_file.read_text(encoding="utf-8"))
        data.setdefault("entries", [])
        data.setdefault("reports", [])
        data.setdefault("archives", [])
        return data
    except Exception as exc:
        logger.warning("bureau_library load failed: %s", exc)
        return _empty_store()


def _save_store(data: dict[str, Any]) -> None:
    library_file = _library_path()
    library_file.parent.mkdir(parents=True, exist_ok=True)
    library_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
