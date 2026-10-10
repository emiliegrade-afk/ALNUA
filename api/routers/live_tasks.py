"""Jarvis Live — background tasks API (DEC-038, SPEC_JARVIS_LIVE Lot 1)."""

from __future__ import annotations

from typing import Any

from fastapi import Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.route_common import *  # noqa: F403

router = APIRouter(tags=["live"])


class LiveTaskCreate(BaseModel):
    agent_id: str = Field(default="coo", min_length=1, max_length=32)
    instruction: str = Field(default="", max_length=4000)
    session_id: str = Field(default="live", max_length=64)
    file_ids: list[str] = Field(default_factory=list, max_length=5)


@router.get("/live/agents")
def live_agents() -> dict[str, list[str]]:
    """Executors the voice front-end is allowed to trigger."""
    from services.live_tasks import allowed_agents

    return {"agents": allowed_agents()}


@router.post("/live/tasks", status_code=201)
def live_task_create(body: LiveTaskCreate) -> dict[str, Any]:
    from services.live_tasks import create_task
    from services.rate_limiter import ASSISTANT_LIMIT, assistant_limiter

    if not assistant_limiter.is_allowed(f"live:{body.session_id}", ASSISTANT_LIMIT):
        raise HTTPException(status_code=429, detail="Trop de tâches — pause 1 minute.")
    try:
        task = create_task(
            body.agent_id,
            body.instruction,
            session_id=body.session_id,
            file_ids=body.file_ids,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return task.to_dict()


@router.get("/live/tasks")
def live_task_list(status: str | None = None, limit: int = 50) -> dict[str, Any]:
    from services.live_tasks import list_tasks

    tasks = list_tasks(status=status, limit=max(1, min(limit, 200)))
    return {"tasks": [t.to_dict() for t in tasks]}


# Declared before /live/tasks/{task_id} so "stream" is not captured as an id.
@router.get("/live/tasks/stream")
async def live_task_stream(request: Request) -> StreamingResponse:
    """SSE feed of task changes (the Next.js proxy adds X-Hub-Key, so EventSource works)."""
    from services.live_tasks_stream import event_stream

    return StreamingResponse(
        event_stream(request),
        media_type="text/event-stream",
        # no-transform: the Next.js proxy would otherwise gzip the stream and hold
        # small SSE frames back until the buffer fills (seen live: updates arrived late).
        headers={"Cache-Control": "no-cache, no-transform", "X-Accel-Buffering": "no"},
    )


@router.get("/live/tasks/{task_id}")
def live_task_get(task_id: str) -> dict[str, Any]:
    from services.live_tasks import get_task

    task = get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    return task.to_dict()


@router.post("/live/tasks/{task_id}/cancel")
def live_task_cancel(task_id: str) -> dict[str, Any]:
    from services.live_tasks import cancel_task

    task = cancel_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Tâche introuvable")
    return task.to_dict()
