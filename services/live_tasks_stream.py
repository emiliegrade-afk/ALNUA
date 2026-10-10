"""Jarvis Live — Server-Sent Events feed of task changes (SPEC_JARVIS_LIVE §9, Lot 1).

Polls the store instead of subscribing to the event bus: it keeps working across
processes and a slow client can never block a worker thread.
"""

from __future__ import annotations

import asyncio
import json
import time
from collections.abc import AsyncIterator
from typing import Any, Protocol

from services.live_tasks import list_tasks
from services.live_tasks_store import LiveTask

POLL_SECONDS = 1.0
HEARTBEAT_SECONDS = 15.0
SNAPSHOT_LIMIT = 100


class _Disconnectable(Protocol):
    async def is_disconnected(self) -> bool: ...


def format_event(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def changed_events(seen: dict[str, str], tasks: list[LiveTask]) -> list[str]:
    """SSE frames for tasks new or modified since ``seen`` (oldest first); updates ``seen``."""
    frames: list[str] = []
    for task in sorted(tasks, key=lambda t: t.created_at):
        if seen.get(task.id) != task.updated_at:
            seen[task.id] = task.updated_at
            frames.append(format_event("task", task.to_dict()))
    return frames


async def event_stream(
    request: _Disconnectable, poll_seconds: float = POLL_SECONDS
) -> AsyncIterator[str]:
    seen: dict[str, str] = {}
    last_sent = time.monotonic()
    yield "retry: 3000\n\n"
    while not await request.is_disconnected():
        tasks = await asyncio.to_thread(list_tasks, None, SNAPSHOT_LIMIT)
        frames = changed_events(seen, tasks)
        for frame in frames:
            yield frame
        now = time.monotonic()
        if frames:
            last_sent = now
        elif now - last_sent >= HEARTBEAT_SECONDS:
            yield ": ping\n\n"
            last_sent = now
        await asyncio.sleep(poll_seconds)
