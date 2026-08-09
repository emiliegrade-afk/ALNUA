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


class Ue58ToolCallRequest(BaseModel):
    tool_id: str = Field(..., min_length=1, max_length=128)
    arguments: dict[str, Any] | None = None


class StudioAgencyRunRequest(BaseModel):
    agent_id: str = Field(default="dev_gaming", min_length=1, max_length=64)
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=8000)
    files_to_create: list[str] | None = None
    files_to_modify: list[str] | None = None


@router.get("/gaming/ue58/status")
def ue58_status() -> dict[str, Any]:
    from skills.skill_ue58 import ue58_health

    return ue58_health()


@router.get("/gaming/studio/agency/status")
def studio_agency_status() -> dict[str, Any]:
    """DEC-020 — Claude Code on local UE project + UE58 editor bridge status."""
    from skills.skill_gaming_agency import agency_status

    return agency_status()


@router.post("/gaming/studio/agency/run")
def studio_agency_run(body: StudioAgencyRunRequest) -> dict[str, Any]:
    """Launch Claude Code / coding agent on UE_PROJECT_PATH (worktree)."""
    from skills.skill_gaming_agency import run_studio_task

    return run_studio_task(
        agent_id=sanitize_user_input(body.agent_id, max_length=64),
        title=sanitize_user_input(body.title, max_length=200),
        description=sanitize_user_input(body.description, max_length=8000),
        files_to_create=body.files_to_create,
        files_to_modify=body.files_to_modify,
    )


@router.post("/gaming/ue58/tools/call")
def ue58_tools_call(body: Ue58ToolCallRequest) -> dict[str, Any]:
    from skills.skill_ue58 import call_tool

    tool_id = sanitize_user_input(body.tool_id, max_length=128)
    return call_tool(tool_id, body.arguments)


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
