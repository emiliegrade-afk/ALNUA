"""Tests for services/event_bus.py."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from services import event_bus


@pytest.fixture(autouse=True)
def clean_event_store():
    event_bus.clear_store()
    yield
    event_bus.clear_store()


def test_emit_and_get_recent_events() -> None:
    with patch.object(event_bus, "_persist_event"):
        event_bus.emit("task_completed", {"task": "test"}, source_agent="marketing")

    recent = event_bus.get_recent_events(limit=5)
    assert len(recent) == 1
    assert recent[0]["event_type"] == "task_completed"
    assert recent[0]["source_agent"] == "marketing"


def test_get_recent_events_filter_by_type() -> None:
    with patch.object(event_bus, "_persist_event"):
        event_bus.emit("task_completed", {}, source_agent="a")
        event_bus.emit("task_failed", {}, source_agent="b")

    completed = event_bus.get_recent_events(event_type="task_completed")
    assert len(completed) == 1
    assert completed[0]["event_type"] == "task_completed"


def test_get_event_stats() -> None:
    with patch.object(event_bus, "_persist_event"):
        event_bus.emit("feature_shipped", {"feature": "x"}, source_agent="dev_app")
        event_bus.emit("feature_shipped", {"feature": "y"}, source_agent="dev_app")

    stats = event_bus.get_event_stats()
    assert stats["total_events_in_memory"] == 2
    assert stats["by_type"]["feature_shipped"] == 2
    assert stats["by_source_agent"]["dev_app"] == 2


def test_clear_store() -> None:
    with patch.object(event_bus, "_persist_event"):
        event_bus.emit("custom", {}, source_agent="system")

    result = event_bus.clear_store()
    assert result["status"] == "ok"
    assert event_bus.get_event_stats()["total_events_in_memory"] == 0
