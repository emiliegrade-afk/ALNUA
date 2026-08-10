"""Library vault export — topic catalog persistence."""

from __future__ import annotations

import json
import logging
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.library_vault_markdown import rel_path_for_entry
from services.library_vault_topics import normalize_topics

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
_LOCK = threading.Lock()


def _catalog_file() -> Path:
    """Resolve via facade so tests can monkeypatch library_vault_export.CATALOG_FILE."""
    from services.library_vault_export import CATALOG_FILE

    return CATALOG_FILE


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_catalog() -> dict[str, Any]:
    return {
        "version": 1,
        "updated_at": "",
        "topics": {},
        "entry_count": 0,
        "topic_count": 0,
    }


def load_catalog() -> dict[str, Any]:
    catalog_path = _catalog_file()
    if not catalog_path.is_file():
        return _empty_catalog()
    try:
        data = json.loads(catalog_path.read_text(encoding="utf-8"))
        data.setdefault("topics", {})
        data.setdefault("version", 1)
        return data
    except Exception as exc:
        logger.warning("topic_catalog load failed: %s", exc)
        return _empty_catalog()


def save_catalog(data: dict[str, Any]) -> None:
    catalog_path = _catalog_file()
    catalog_path.parent.mkdir(parents=True, exist_ok=True)
    catalog_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _topic_row_defaults(slug: str) -> dict[str, Any]:
    return {
        "slug": slug,
        "label": slug.replace("-", " "),
        "entry_ids": [],
        "paths": [],
        "bureaus": [],
        "timings": [],
        "titles": [],
        "has_now": False,
        "learn_count": 0,
        "promoted_skill": None,
    }


def _merge_entry_into_topic_row(
    row: dict[str, Any],
    *,
    eid: str,
    rel: str,
    entry: dict[str, Any],
) -> None:
    if eid and eid not in row["entry_ids"]:
        row["entry_ids"].append(eid)
    if rel not in row["paths"]:
        row["paths"].append(rel)
    bureau = str(entry.get("bureau") or "hub")
    if bureau not in row["bureaus"]:
        row["bureaus"].append(bureau)
    timing = str(entry.get("timing") or "later")
    if timing not in row["timings"]:
        row["timings"].append(timing)
    if timing == "now":
        row["has_now"] = True
    title = str(entry.get("title") or "")[:120]
    if title and title not in row["titles"]:
        row["titles"].append(title)
        row["titles"] = row["titles"][:12]


def _build_catalog(entries: list[dict[str, Any]], path_map: dict[str, str]) -> dict[str, Any]:
    topics: dict[str, dict[str, Any]] = {}
    for entry in entries:
        eid = str(entry.get("id") or "")
        if not eid:
            continue
        rel = path_map.get(eid, rel_path_for_entry(entry))
        for slug in normalize_topics(entry):
            row = topics.setdefault(slug, _topic_row_defaults(slug))
            _merge_entry_into_topic_row(row, eid=eid, rel=rel, entry=entry)

    prev = load_catalog().get("topics", {})
    for slug, row in topics.items():
        old = prev.get(slug) or {}
        row["learn_count"] = int(old.get("learn_count") or 0)
        row["promoted_skill"] = old.get("promoted_skill")

    return {
        "version": 1,
        "updated_at": _utc_now(),
        "topics": topics,
        "entry_count": len(entries),
        "topic_count": len(topics),
    }


def topics_markdown(catalog: dict[str, Any]) -> str:
    topics = catalog.get("topics") or {}
    lines = [
        "# Catalogue sujets — Bibliothèque ALNUA",
        "",
        f"_Généré automatiquement — {catalog.get('updated_at', '')}_",
        "",
        f"**{catalog.get('topic_count', 0)}** sujets · **{catalog.get('entry_count', 0)}** fiches",
        "",
        "Les agents scannent ce catalogue, puis chargent un sujet à la demande (`learn_topic`).",
        "",
        "| Sujet | Fiches | Now | Bureaux | Exemples |",
        "|-------|--------|-----|---------|----------|",
    ]
    ordered = sorted(
        topics.values(),
        key=lambda t: (-int(t.get("has_now") or 0), -len(t.get("entry_ids") or []), t.get("slug", "")),
    )
    for row in ordered[:500]:
        slug = row.get("slug", "")
        n = len(row.get("entry_ids") or [])
        now = "oui" if row.get("has_now") else ""
        bureaus = ", ".join(row.get("bureaus") or [])
        examples = "; ".join((row.get("titles") or [])[:2]).replace("|", "/")
        lines.append(f"| `{slug}` | {n} | {now} | {bureaus} | {examples} |")

    if len(ordered) > 500:
        lines.append("")
        lines.append(f"_… {len(ordered) - 500} sujets supplémentaires dans `data/topic_catalog.json`._")

    lines.append("")
    return "\n".join(lines)


def patch_catalog_for_entry(
    catalog: dict[str, Any],
    entry: dict[str, Any],
    rel: str,
    synced: str,
) -> None:
    """Merge one entry into an in-memory catalog dict."""
    topics = catalog.setdefault("topics", {})
    eid = str(entry.get("id") or "")
    for slug in normalize_topics(entry):
        row = topics.setdefault(slug, _topic_row_defaults(slug))
        _merge_entry_into_topic_row(row, eid=eid, rel=rel, entry=entry)
    catalog["updated_at"] = synced
    catalog["topic_count"] = len(topics)
    catalog["entry_count"] = max(
        int(catalog.get("entry_count") or 0),
        len({eid for t in topics.values() for eid in (t.get("entry_ids") or [])}),
    )
