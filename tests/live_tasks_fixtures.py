"""Shared fixtures for the Nadia Live (Jarvis Live) tests."""

from __future__ import annotations

import pytest

from services import live_tasks as lt
from services.live_tasks_store import LiveTaskStore


@pytest.fixture()
def registry(tmp_path, monkeypatch):
    """Isolated store, no worker pool (tests call run_task themselves), recorded events."""
    store = LiveTaskStore(tmp_path / "live_tasks.json")
    monkeypatch.setattr(lt, "_store", store)
    submitted: list[str] = []
    monkeypatch.setattr(lt, "_submit", lambda fn, *args: submitted.append(args[0]))
    events: list[dict] = []
    monkeypatch.setattr(
        "services.event_bus.emit",
        lambda event_type, payload=None, **kw: events.append({"type": event_type, **(payload or {})}),
    )
    store.submitted = submitted  # type: ignore[attr-defined]
    store.events = events  # type: ignore[attr-defined]
    return store

