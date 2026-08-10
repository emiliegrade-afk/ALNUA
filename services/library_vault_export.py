"""
Export bureau library JSON → Obsidian vault markdown + topic catalog.

Source of truth for article bodies remains the vault notes (full summary/digest).
The catalog is a lightweight index agents can scan before deep-learning a topic.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from services.bureau_library import BUREAU_LABELS, LIBRARY_FILE, _load_store
from services.library_vault_catalog import (
    ROOT,
    _LOCK,
    _build_catalog,
    _utc_now,
    load_catalog,
    patch_catalog_for_entry,
    save_catalog,
    topics_markdown,
)
from services.library_vault_markdown import entry_to_markdown, rel_path_for_entry
from services.library_vault_topics import normalize_topics, slugify_topic
from services.obsidian_vault import ensure_vault_layout, get_vault_path

logger = logging.getLogger(__name__)

CATALOG_FILE = ROOT / "data" / "topic_catalog.json"

__all__ = [
    "CATALOG_FILE",
    "export_entry_to_vault",
    "export_library_to_vault",
    "load_catalog",
    "normalize_topics",
    "rel_path_for_entry",
    "save_catalog",
    "slugify_topic",
]


def export_entry_to_vault(
    entry: dict[str, Any],
    *,
    vault: Path | None = None,
    update_catalog: bool = True,
) -> dict[str, Any]:
    """Write one library entry as a markdown note; optionally patch the catalog."""
    root = vault or get_vault_path()
    ensure_vault_layout(root)
    synced = _utc_now()
    rel = rel_path_for_entry(entry)
    out = root / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(entry_to_markdown(entry, synced_at=synced), encoding="utf-8")

    result: dict[str, Any] = {"path": rel, "id": entry.get("id"), "synced_at": synced}

    if update_catalog:
        with _LOCK:
            catalog = load_catalog()
            patch_catalog_for_entry(catalog, entry, rel, synced)
            save_catalog(catalog)
            topics_path = root / "library" / "_index" / "TOPICS.md"
            topics_path.write_text(topics_markdown(catalog), encoding="utf-8")
            result["catalog_updated"] = True

    return result


def export_library_to_vault(
    *,
    vault: Path | None = None,
    limit: int | None = None,
    index_chroma: bool = False,
) -> dict[str, Any]:
    """Full export of bureau library → vault notes + topic catalog (+ optional Chroma)."""
    root = vault or get_vault_path()
    layout = ensure_vault_layout(root)
    store = _load_store()
    entries = list(store.get("entries", []))
    if limit is not None:
        entries = entries[:limit]

    path_map: dict[str, str] = {}
    written = 0
    errors = 0
    synced = _utc_now()

    for entry in entries:
        try:
            rel = rel_path_for_entry(entry)
            out = root / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(entry_to_markdown(entry, synced_at=synced), encoding="utf-8")
            eid = str(entry.get("id") or "")
            if eid:
                path_map[eid] = rel
            written += 1
        except Exception as exc:
            errors += 1
            logger.warning("export entry failed: %s", exc)

    catalog = _build_catalog(entries, path_map)
    with _LOCK:
        save_catalog(catalog)
        topics_path = root / "library" / "_index" / "TOPICS.md"
        topics_path.write_text(topics_markdown(catalog), encoding="utf-8")

    chroma_result: dict[str, Any] | None = None
    if index_chroma:
        try:
            from skills.skill_chroma import index_library_vault

            chroma_result = index_library_vault(vault=root)
        except Exception as exc:
            logger.warning("Chroma library index failed: %s", exc)
            chroma_result = {"ok": False, "error": str(exc)}

    return {
        "ok": True,
        "vault": str(root),
        "written": written,
        "errors": errors,
        "topic_count": catalog.get("topic_count", 0),
        "entry_count": catalog.get("entry_count", 0),
        "catalog_path": str(CATALOG_FILE),
        "topics_md": "library/_index/TOPICS.md",
        "layout": layout,
        "chroma": chroma_result,
        "library_source": str(LIBRARY_FILE),
        "bureaus": {b: BUREAU_LABELS[b] for b in sorted(BUREAU_LABELS)},
    }
