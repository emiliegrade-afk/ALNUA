"""ALNUA Studio presets — static templates for prompt + params."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_TEMPLATES_PATH = Path(__file__).resolve().parents[2] / "data" / "studio_templates.json"


@lru_cache(maxsize=1)
def _load_raw() -> list[dict[str, Any]]:
    if not _TEMPLATES_PATH.is_file():
        return []
    data = json.loads(_TEMPLATES_PATH.read_text(encoding="utf-8"))
    return list(data.get("templates") or [])


def get_studio_templates(platform: str | None = None, tool_id: str | None = None) -> list[dict[str, Any]]:
    rows = _load_raw()
    out: list[dict[str, Any]] = []
    for row in rows:
        platforms = row.get("platforms") or []
        if platform and platforms and platform not in platforms and "both" not in platforms:
            continue
        tool_ids = row.get("tool_ids") or []
        if tool_id and tool_ids and tool_id not in tool_ids:
            continue
        out.append(row)
    return out


def invalidate_studio_templates_cache() -> None:
    _load_raw.cache_clear()
