"""Library vault export — markdown note generation."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any

from services.bureau_library import VALID_BUREAUS
from services.library_vault_topics import normalize_topics


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


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
