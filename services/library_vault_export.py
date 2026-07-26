"""
Export bureau library JSON → Obsidian vault markdown + topic catalog.

Source of truth for article bodies remains the vault notes (full summary/digest).
The catalog is a lightweight index agents can scan before deep-learning a topic.
"""

from __future__ import annotations

import json
import logging
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.bureau_library import BUREAU_LABELS, LIBRARY_FILE, VALID_BUREAUS, _load_store
from services.obsidian_vault import ensure_vault_layout, get_vault_path

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
CATALOG_FILE = ROOT / "data" / "topic_catalog.json"
_LOCK = threading.Lock()

# Stopwords for topic normalization (FR + EN noise from research queries)
_STOP = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "of",
        "for",
        "to",
        "in",
        "on",
        "with",
        "de",
        "du",
        "des",
        "le",
        "la",
        "les",
        "un",
        "une",
        "et",
        "ou",
        "pour",
        "par",
        "sur",
        "dans",
        "avec",
        "qui",
        "que",
        "au",
        "aux",
        "en",
        "latest",
        "update",
        "updates",
        "new",
        "features",
        "2024",
        "2025",
        "2026",
        "2027",
    }
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def slugify_topic(raw: str) -> str:
    """Normalize a topic / query string into a stable catalog slug."""
    text = (raw or "").strip().lower()
    text = re.sub(r"[^\w\s\-]+", " ", text, flags=re.UNICODE)
    words = [w for w in re.split(r"[\s_\-]+", text) if w and w not in _STOP and len(w) > 1]
    if not words:
        words = [w for w in re.split(r"[\s_\-]+", text) if w][:4] or ["general"]
    slug = "-".join(words[:6])
    return slug[:80].strip("-") or "general"


def normalize_topics(entry: dict[str, Any]) -> list[str]:
    """Return unique topic slugs for an entry (from topics list + query fallback)."""
    slugs: list[str] = []
    seen: set[str] = set()
    raw_topics = entry.get("topics") or []
    if isinstance(raw_topics, list):
        for t in raw_topics:
            slug = slugify_topic(str(t))
            if slug and slug not in seen:
                seen.add(slug)
                slugs.append(slug)
    query = str(entry.get("query") or "").strip()
    if query:
        slug = slugify_topic(query)
        if slug and slug not in seen:
            seen.add(slug)
            slugs.append(slug)
    if not slugs:
        title_slug = slugify_topic(str(entry.get("title") or "general"))
        slugs.append(title_slug)
    return slugs[:8]


def _safe_filename(title: str, entry_id: str) -> str:
    base = re.sub(r"[^\w\s\-]+", "", (title or "entry"), flags=re.UNICODE)
    base = re.sub(r"\s+", "-", base.strip())[:60].strip("-") or "entry"
    short_id = (entry_id or "x")[:8]
    return f"{base}-{short_id}.md"


def _yaml_escape(value: str) -> str:
    return (value or "").replace('"', '\\"').replace("\n", " ").strip()


def _entry_body(entry: dict[str, Any]) -> str:
    """Full body — never truncate summary/digest for vault storage."""
    digest = str(entry.get("digest") or "").strip()
    summary = str(entry.get("summary") or "").strip()
    parts: list[str] = []
    if digest:
        parts.append("## Digest\n\n" + digest)
    if summary:
        parts.append("## Summary\n\n" + summary)
    if not parts:
        parts.append("_Aucune synthèse disponible._")

    source_url = str(entry.get("source_url") or "").strip()
    source_title = str(entry.get("source_title") or "").strip()
    if source_url:
        label = source_title or source_url
        parts.append(f"## Source\n\n[{label}]({source_url})")

    query = str(entry.get("query") or "").strip()
    if query:
        parts.append(f"## Query\n\n`{query}`")

    return "\n\n".join(parts)


def entry_to_markdown(entry: dict[str, Any], *, synced_at: str | None = None) -> str:
    topics = normalize_topics(entry)
    topics_yaml = "[" + ", ".join(topics) + "]"
    synced = synced_at or _utc_now()
    title = str(entry.get("title") or "Sans titre").strip()
    front = "\n".join(
        [
            "---",
            "type: library",
            f'id: {entry.get("id", "")}',
            f'bureau: {entry.get("bureau", "hub")}',
            f'timing: {entry.get("timing", "later")}',
            f"topics: {topics_yaml}",
            f'source_url: "{_yaml_escape(str(entry.get("source_url") or ""))}"',
            f'agent_id: "{_yaml_escape(str(entry.get("agent_id") or ""))}"',
            f'created_at: "{_yaml_escape(str(entry.get("created_at") or ""))}"',
            f'hub_synced_at: "{synced}"',
            "---",
            "",
            f"# {title}",
            "",
            _entry_body(entry),
            "",
        ]
    )
    return front


def rel_path_for_entry(entry: dict[str, Any]) -> str:
    bureau = entry.get("bureau", "hub")
    if bureau not in VALID_BUREAUS:
        bureau = "hub"
    filename = _safe_filename(str(entry.get("title") or "entry"), str(entry.get("id") or "x"))
    return f"library/{bureau}/{filename}"


def _empty_catalog() -> dict[str, Any]:
    return {
        "version": 1,
        "updated_at": "",
        "topics": {},
        "entry_count": 0,
        "topic_count": 0,
    }


def load_catalog() -> dict[str, Any]:
    if not CATALOG_FILE.is_file():
        return _empty_catalog()
    try:
        data = json.loads(CATALOG_FILE.read_text(encoding="utf-8"))
        data.setdefault("topics", {})
        data.setdefault("version", 1)
        return data
    except Exception as exc:
        logger.warning("topic_catalog load failed: %s", exc)
        return _empty_catalog()


def save_catalog(data: dict[str, Any]) -> None:
    CATALOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CATALOG_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _build_catalog(entries: list[dict[str, Any]], path_map: dict[str, str]) -> dict[str, Any]:
    topics: dict[str, dict[str, Any]] = {}
    for entry in entries:
        eid = str(entry.get("id") or "")
        if not eid:
            continue
        rel = path_map.get(eid, rel_path_for_entry(entry))
        for slug in normalize_topics(entry):
            row = topics.setdefault(
                slug,
                {
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
                },
            )
            if eid not in row["entry_ids"]:
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

    # Preserve learn_count / promoted_skill from previous catalog
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


def _topics_markdown(catalog: dict[str, Any]) -> str:
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
            topics = catalog.setdefault("topics", {})
            eid = str(entry.get("id") or "")
            for slug in normalize_topics(entry):
                row = topics.setdefault(
                    slug,
                    {
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
                    },
                )
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
            catalog["updated_at"] = synced
            catalog["topic_count"] = len(topics)
            catalog["entry_count"] = max(
                int(catalog.get("entry_count") or 0),
                len({eid for t in topics.values() for eid in (t.get("entry_ids") or [])}),
            )
            save_catalog(catalog)
            topics_path = root / "library" / "_index" / "TOPICS.md"
            topics_path.write_text(_topics_markdown(catalog), encoding="utf-8")
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
        topics_path.write_text(_topics_markdown(catalog), encoding="utf-8")

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
