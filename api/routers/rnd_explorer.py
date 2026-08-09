"""Phase 28 — R&D Explorer (keep rnd.py lean)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from services.input_sanitizer import sanitize_user_input

router = APIRouter(tags=["rnd-explorer"])


class ExplorerBriefBody(BaseModel):
    topics: list[str] = Field(default_factory=list)
    sources: list[str] = Field(default_factory=list)
    agent_id: str = "brainstorm"
    limit: int = Field(default=25, ge=5, le=40)


def _clean_topics(raw: list[str] | None) -> list[str]:
    out: list[str] = []
    for t in raw or []:
        s = sanitize_user_input(str(t), max_length=64).strip()
        if s:
            out.append(s)
    return out[:12]


@router.get("/rnd/explorer/signals")
def explorer_signals(
    topics: str = Query(default="", description="Comma-separated topics"),
    sources: str = Query(default="", description="Comma-separated: hn,reddit,github"),
    limit: int = Query(default=40, ge=5, le=80),
) -> dict[str, Any]:
    from services.rnd_explorer import scan_signals

    topic_list = _clean_topics([t for t in topics.split(",") if t.strip()]) if topics else []
    source_list = [s.strip() for s in sources.split(",") if s.strip()] if sources else []
    return scan_signals(
        topics=topic_list or None,
        sources=source_list or None,
        limit=limit,
    )


@router.post("/rnd/explorer/brief")
def explorer_brief(body: ExplorerBriefBody) -> dict[str, Any]:
    from services.rnd_explorer import brief_explorer

    return brief_explorer(
        topics=_clean_topics(body.topics) or None,
        sources=[sanitize_user_input(s, max_length=32) for s in body.sources if s] or None,
        agent_id=sanitize_user_input(body.agent_id, max_length=32),
        limit=body.limit,
    )
