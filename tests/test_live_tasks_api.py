# ruff: noqa: F811
"""Jarvis Live Lot 1 — HTTP API and SSE feed (SPEC_JARVIS_LIVE / DEC-038)."""

from __future__ import annotations

import asyncio
import json

from services import live_tasks_stream as stream
from tests.conftest import HUB_HEADERS
from tests.live_tasks_fixtures import registry  # noqa: F401  (pytest fixture, redefined as test arg)


# ── API ─────────────────────────────────────────────────────────────────────


def test_api_create_get_list_cancel(hub_client, registry, monkeypatch):
    res = hub_client.post(
        "/live/tasks", json={"agent_id": "coo", "instruction": "état du pipeline"}, headers=HUB_HEADERS
    )
    assert res.status_code == 201
    task_id = res.json()["id"]

    assert hub_client.get(f"/live/tasks/{task_id}", headers=HUB_HEADERS).json()["status"] == "queued"
    listing = hub_client.get("/live/tasks?status=queued", headers=HUB_HEADERS).json()["tasks"]
    assert [t["id"] for t in listing] == [task_id]

    cancelled = hub_client.post(f"/live/tasks/{task_id}/cancel", headers=HUB_HEADERS)
    assert cancelled.json()["status"] == "cancelled"


def test_api_rejects_unlisted_agent_and_unknown_task(hub_client, registry):
    bad = hub_client.post(
        "/live/tasks", json={"agent_id": "dev_app", "instruction": "x y"}, headers=HUB_HEADERS
    )
    assert bad.status_code == 400
    assert hub_client.get("/live/tasks/inconnu", headers=HUB_HEADERS).status_code == 404
    assert hub_client.post("/live/tasks/inconnu/cancel", headers=HUB_HEADERS).status_code == 404


def test_api_requires_hub_key(hub_client, registry):
    assert hub_client.get("/live/tasks").status_code in (401, 403)


def test_api_agents_endpoint(hub_client):
    res = hub_client.get("/live/agents", headers=HUB_HEADERS)
    assert res.status_code == 200
    assert set(res.json()["agents"]) <= {"coo", "secretary", "plan"}


# ── SSE ─────────────────────────────────────────────────────────────────────


def test_changed_events_only_emits_new_or_modified(registry):
    first = registry.add("coo", "a b")
    seen: dict[str, str] = {}
    frames = stream.changed_events(seen, registry.list_tasks())
    assert len(frames) == 1 and frames[0].startswith("event: task\n")
    assert stream.changed_events(seen, registry.list_tasks()) == []

    registry.update(first.id, status="running")
    frames = stream.changed_events(seen, registry.list_tasks())
    payload = json.loads(frames[0].split("data: ", 1)[1])
    assert payload["status"] == "running"


def test_stream_headers_stop_the_proxy_from_buffering():
    # Seen live: without no-transform the Next.js proxy gzips the stream and delivers
    # small SSE frames late (a task showed up only once it was already finished).
    from api.routers.live_tasks import live_task_stream

    response = asyncio.run(live_task_stream(object()))  # type: ignore[arg-type]
    assert "no-transform" in response.headers["cache-control"]
    assert response.media_type == "text/event-stream"


def test_event_stream_yields_snapshot_then_stops_on_disconnect(registry):
    registry.add("coo", "a b")

    class FakeRequest:
        def __init__(self) -> None:
            self.calls = 0

        async def is_disconnected(self) -> bool:
            self.calls += 1
            return self.calls > 1  # one loop turn, then the client leaves

    async def collect() -> list[str]:
        return [chunk async for chunk in stream.event_stream(FakeRequest(), poll_seconds=0)]

    chunks = asyncio.run(collect())
    assert chunks[0].startswith("retry:")
    assert any(c.startswith("event: task") for c in chunks)

