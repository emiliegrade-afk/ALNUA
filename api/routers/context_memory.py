"""Context Engine / stratified memory API — Phase F (DEC-027)."""

from __future__ import annotations

from typing import Any

from api.route_common import *  # noqa: F403
from pydantic import BaseModel, Field

router = APIRouter(tags=["context-memory"])


class CompileContextBody(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=64)
    task: str = Field(..., min_length=1, max_length=2000)
    task_id: str | None = Field(default=None, max_length=128)
    loop_feedback: str | None = Field(default=None, max_length=4000)
    include_library: bool = True


class WorkingMemoryBody(BaseModel):
    task_id: str = Field(..., min_length=1, max_length=128)
    agent_id: str = Field(default="", max_length=64)
    feedback: str = Field(default="", max_length=4000)
    notes: str = Field(default="", max_length=2000)
    attempt: int | None = None


@router.get("/context/defaults")
def context_defaults() -> dict[str, Any]:
    from services.collective_learning import promote_min_agents
    from services.context_engine import context_engine_enabled

    try:
        from config.settings import get_settings

        s = get_settings()
        return {
            "enabled": bool(s.context_engine_enabled),
            "promote_min_agents": int(s.collective_promote_min_agents),
            "layers": ["L1", "L2", "L3", "L4"],
        }
    except Exception:
        return {
            "enabled": context_engine_enabled(),
            "promote_min_agents": promote_min_agents(),
            "layers": ["L1", "L2", "L3", "L4"],
        }


@router.post("/context/compile")
def context_compile(body: CompileContextBody) -> dict[str, Any]:
    from services.input_sanitizer import sanitize_user_input
    from services.context_engine import compile_context

    aid = sanitize_user_input(body.agent_id, redact_pii_enabled=False)[:64]
    task = sanitize_user_input(body.task, redact_pii_enabled=False)[:2000]
    fb = (
        sanitize_user_input(body.loop_feedback, redact_pii_enabled=False)[:4000]
        if body.loop_feedback
        else None
    )
    bundle = compile_context(
        aid,
        task,
        task_id=body.task_id,
        loop_feedback=fb,
        include_library=body.include_library,
    )
    out = bundle.to_dict()
    out["preview"] = bundle.as_block()[:4000]
    return out


@router.post("/context/working-memory")
def context_set_working(body: WorkingMemoryBody) -> dict[str, Any]:
    from services.input_sanitizer import sanitize_user_input
    from services.working_memory import set_working_memory

    tid = sanitize_user_input(body.task_id, redact_pii_enabled=False)[:128]
    entry = set_working_memory(
        tid,
        agent_id=sanitize_user_input(body.agent_id, redact_pii_enabled=False)[:64],
        feedback=sanitize_user_input(body.feedback, redact_pii_enabled=False)[:4000],
        notes=sanitize_user_input(body.notes, redact_pii_enabled=False)[:2000],
        attempt=body.attempt,
    )
    return {"ok": True, "entry": entry}


@router.delete("/context/working-memory/{task_id}")
def context_wipe_working(task_id: str) -> dict[str, Any]:
    from services.input_sanitizer import sanitize_user_input
    from services.working_memory import wipe_working_memory

    tid = sanitize_user_input(task_id, redact_pii_enabled=False)[:128]
    return {"wiped": wipe_working_memory(tid), "task_id": tid}


@router.get("/context/collective")
def context_collective(
    room: str | None = None,
    limit: int = Query(default=30, ge=1, le=100),
) -> dict[str, Any]:
    from services.collective_learning import list_collective_lessons
    from services.input_sanitizer import sanitize_user_input

    r = sanitize_user_input(room, redact_pii_enabled=False)[:64] if room else None
    return {"lessons": list_collective_lessons(room=r, limit=limit)}
