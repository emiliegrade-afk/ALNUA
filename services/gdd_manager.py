"""
services/gdd_manager.py — Chunk, store, and search GDD markdown per gaming project.

v1 scope: markdown only, fixed char-based chunking, Supabase text search (no embeddings/Mem0).
Consumers: level_designer, game_director, dev_gaming (via API / MCP later).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# ~512 tokens / ~64 token overlap (char heuristic: 4 chars ≈ 1 token)
CHUNK_SIZE_CHARS = 2048
OVERLAP_CHARS = 256
MAX_INGEST_CHARS = 500_000


@dataclass
class GddChunkDraft:
    section_title: str
    chunk_index: int
    content: str
    token_estimate: int


def _estimate_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def _split_with_overlap(text: str, size: int, overlap: int) -> list[str]:
    """Split long text into overlapping windows."""
    normalized = text.strip()
    if not normalized:
        return []
    if len(normalized) <= size:
        return [normalized]

    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + size, len(normalized))
        piece = normalized[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(normalized):
            break
        start = max(0, end - overlap)
    return chunks


def parse_markdown_sections(markdown: str) -> list[tuple[str, str]]:
    """
    Split markdown by ## / # headers. Returns (section_title, body) pairs.
    """
    text = markdown.replace("\r\n", "\n").strip()
    if not text:
        return []

    pattern = re.compile(r"^(#{1,3})\s+(.+)$", re.MULTILINE)
    matches = list(pattern.finditer(text))

    if not matches:
        return [("Document", text)]

    sections: list[tuple[str, str]] = []
    for i, match in enumerate(matches):
        title = match.group(2).strip()
        body_start = match.end()
        body_end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[body_start:body_end].strip()
        if body or title:
            sections.append((title or "Section", body or title))

    return sections or [("Document", text)]


def chunk_gdd_markdown(markdown: str) -> list[GddChunkDraft]:
    """Parse sections then chunk each section body."""
    drafts: list[GddChunkDraft] = []
    for section_title, body in parse_markdown_sections(markdown):
        parts = _split_with_overlap(body, CHUNK_SIZE_CHARS, OVERLAP_CHARS)
        if not parts and body:
            parts = [body]
        for idx, content in enumerate(parts):
            drafts.append(
                GddChunkDraft(
                    section_title=section_title[:200],
                    chunk_index=idx,
                    content=content,
                    token_estimate=_estimate_tokens(content),
                )
            )
    return drafts


def ingest_gdd(
    db: Any,
    *,
    project_id: str,
    markdown: str,
    document_title: str = "GDD",
    source_filename: str | None = None,
    replace_existing: bool = True,
) -> dict[str, Any]:
    """
    Chunk markdown and persist rows in gdd_chunks.
    Deletes prior chunks for project when replace_existing=True.
    """
    if len(markdown) > MAX_INGEST_CHARS:
        raise ValueError(
            f"GDD too large ({len(markdown)} chars). Max {MAX_INGEST_CHARS}."
        )

    projects = db.select("projects", filters={"id": project_id}, limit=1)
    if not projects:
        raise ValueError(f"Project not found: {project_id}")
    if projects[0].get("branch") != "gaming":
        raise ValueError("GDD ingest is only allowed for gaming branch projects")

    drafts = chunk_gdd_markdown(markdown)
    if not drafts:
        raise ValueError("No content to ingest")

    if replace_existing:
        try:
            db.table("gdd_chunks").delete().eq("project_id", project_id).execute()
        except Exception as exc:
            logger.warning("gdd_chunks delete skipped (table may be missing): %s", exc)

    rows = [
        {
            "project_id": project_id,
            "document_title": document_title[:200],
            "source_filename": source_filename,
            "section_title": d.section_title,
            "chunk_index": d.chunk_index,
            "content": d.content,
            "token_estimate": d.token_estimate,
        }
        for d in drafts
    ]

    inserted = db.insert_many("gdd_chunks", rows)

    sections = sorted({d.section_title for d in drafts})
    return {
        "project_id": project_id,
        "document_title": document_title,
        "chunks_count": len(inserted),
        "sections": sections,
        "total_tokens_estimate": sum(d.token_estimate for d in drafts),
    }


def list_gdd_sections(db: Any, project_id: str) -> list[dict[str, Any]]:
    """Aggregate chunk counts per section."""
    chunks = db.select(
        "gdd_chunks",
        columns="section_title, chunk_index, token_estimate",
        filters={"project_id": project_id},
        order_by="section_title",
        ascending=True,
    )
    if not chunks:
        return []

    by_section: dict[str, dict[str, Any]] = {}
    for row in chunks:
        title = row.get("section_title") or "Document"
        if title not in by_section:
            by_section[title] = {
                "section_title": title,
                "chunk_count": 0,
                "token_estimate": 0,
            }
        by_section[title]["chunk_count"] += 1
        by_section[title]["token_estimate"] += int(row.get("token_estimate") or 0)

    return list(by_section.values())


def list_gdd_chunks(
    db: Any,
    project_id: str,
    *,
    section_title: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    filters: dict[str, Any] = {"project_id": project_id}
    if section_title:
        filters["section_title"] = section_title

    rows = db.select(
        "gdd_chunks",
        filters=filters,
        order_by="section_title",
        ascending=True,
        limit=limit,
    )
    rows.sort(
        key=lambda r: (r.get("section_title", ""), r.get("chunk_index", 0)),
    )
    return [
        {
            "id": r["id"],
            "section_title": r.get("section_title"),
            "chunk_index": r.get("chunk_index", 0),
            "content": r.get("content", ""),
            "token_estimate": r.get("token_estimate", 0),
            "document_title": r.get("document_title"),
            "source_filename": r.get("source_filename"),
        }
        for r in rows
    ]


def search_gdd_chunks(
    db: Any,
    project_id: str,
    query: str,
    *,
    limit: int = 20,
) -> list[dict[str, Any]]:
    """
    v1 text search — case-insensitive substring match in Python.
    (Supabase ilike used when available; falls back to client filter.)
    """
    q = query.strip().lower()
    if len(q) < 2:
        return []

    try:
        response = (
            db.table("gdd_chunks")
            .select("id, section_title, chunk_index, content, token_estimate, document_title")
            .eq("project_id", project_id)
            .ilike("content", f"%{query}%")
            .limit(limit)
            .execute()
        )
        rows = response.data or []
    except Exception:
        rows = db.select(
            "gdd_chunks",
            columns="id, section_title, chunk_index, content, token_estimate, document_title",
            filters={"project_id": project_id},
            limit=500,
        )
        rows = [r for r in rows if q in (r.get("content") or "").lower()][:limit]

    return [
        {
            "id": r["id"],
            "section_title": r.get("section_title"),
            "chunk_index": r.get("chunk_index", 0),
            "snippet": _snippet(r.get("content", ""), query),
            "token_estimate": r.get("token_estimate", 0),
            "score": _relevance_score(r.get("content", ""), q),
        }
        for r in sorted(rows, key=lambda x: x.get("score", 0), reverse=True)
    ]


def _snippet(content: str, query: str, radius: int = 120) -> str:
    lower = content.lower()
    idx = lower.find(query.lower())
    if idx < 0:
        return content[: radius * 2] + ("…" if len(content) > radius * 2 else "")
    start = max(0, idx - radius)
    end = min(len(content), idx + len(query) + radius)
    prefix = "…" if start > 0 else ""
    suffix = "…" if end < len(content) else ""
    return prefix + content[start:end] + suffix


def _relevance_score(content: str, query: str) -> float:
    lower = content.lower()
    q = query.lower()
    count = lower.count(q)
    if not count:
        return 0.0
    return float(count) + 1.0 / max(1, len(lower))
