"""UE5.8 studio bridge — Vague A / DEC-017 (dedicated router, keep agents_pole lean)."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from services.input_sanitizer import sanitize_user_input

router = APIRouter(tags=["ue58"])


class Ue58ChatRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64)
    message: str = Field(..., min_length=1, max_length=4000)
    session_id: str | None = Field(default=None, max_length=128)


class Ue58GddSyncRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=128)
    direction: str = Field(..., description="pull | push")
    payload: dict[str, Any] | None = None


@router.get("/gaming/ue58/status")
def ue58_status() -> dict[str, Any]:
    from skills.skill_ue58 import ue58_health

    return ue58_health()


@router.post("/agents/ai-programmer/ue58-probe")
def ai_programmer_ue58_probe() -> dict[str, Any]:
    from agents.ai_programmer_agent import AiProgrammerAgent

    return AiProgrammerAgent().probe_ue58()


@router.post("/agents/technical-artist/ue58-probe")
def technical_artist_ue58_probe() -> dict[str, Any]:
    from agents.technical_artist_agent import TechnicalArtistAgent

    return TechnicalArtistAgent().probe_ue58()


@router.post("/agents/vfx-artist/ue58-probe")
def vfx_artist_ue58_probe() -> dict[str, Any]:
    from agents.vfx_artist_agent import VfxArtistAgent

    return VfxArtistAgent().probe_ue58()


@router.post("/gaming/ue58/chat")
def ue58_chat(body: Ue58ChatRequest) -> dict[str, Any]:
    from skills.skill_ue58 import chat

    message = sanitize_user_input(body.message, max_length=4000)
    agent_id = sanitize_user_input(body.agent_id, max_length=64)
    return chat(agent_id, message, body.session_id)


@router.post("/gaming/ue58/gdd/sync")
def ue58_gdd_sync(body: Ue58GddSyncRequest) -> dict[str, Any]:
    from skills.skill_ue58 import gdd_sync

    project_id = sanitize_user_input(body.project_id, max_length=128)
    direction = sanitize_user_input(body.direction, max_length=16)
    return gdd_sync(project_id, direction, body.payload)
