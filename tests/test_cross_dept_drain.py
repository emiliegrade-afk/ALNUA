"""Phase 36 Depth+ — cross-dept drain (skeletons without LLM)."""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def cross_dept_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    queue = tmp_path / "cross_dept_queue.json"
    arts = tmp_path / "cross_dept_artifacts"
    monkeypatch.setattr("services.cross_dept_handlers._QUEUE", queue)
    monkeypatch.setattr("services.cross_dept_drain._ARTIFACTS", arts)
    monkeypatch.setenv("CROSS_DEPT_DRAIN_LLM", "0")
    return queue


def test_emit_and_drain_skeletons(cross_dept_paths: Path) -> None:
    import services.cross_dept_handlers  # noqa: F401 — register @subscribe
    from services.cross_dept_drain import drain_cross_dept_queue, emit_project_validated
    from services.cross_dept_handlers import list_cross_dept_queue

    out = emit_project_validated(title="App Test Launch", project_id="p-test")
    assert out["emitted"] is True
    queued = list_cross_dept_queue(limit=10, status="queued")
    assert len(queued) >= 3
    depts = {i["department"] for i in queued}
    assert {"marketing", "finances", "analytics"} <= depts
    assert all(i.get("id") for i in queued)

    drained = drain_cross_dept_queue(limit=3)
    assert drained["processed"] == 3
    assert drained["ok"] == 3
    assert drained["llm_enabled"] is False

    done = list_cross_dept_queue(limit=10, status="done")
    assert len(done) >= 3
    assert all(d.get("artifact_path") for d in done[:3])


def test_checklist_actions_no_llm(cross_dept_paths: Path) -> None:
    from services.cross_dept_drain import execute_item
    from services.cross_dept_handlers import list_cross_dept_queue, on_content_validated
    from services.event_bus import Event

    on_content_validated(
        Event(
            event_type="content_validated",
            payload={"title": "Post X", "project_id": "p1"},
            source_agent="qa",
        )
    )
    items = list_cross_dept_queue(limit=5, status="queued")
    assert items
    target = next(i for i in items if i["status"] == "queued")
    res = execute_item(target)
    assert res["ok"] is True
    assert Path(res["artifact_path"]).is_file()
