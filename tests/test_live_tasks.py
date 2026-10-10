# ruff: noqa: F811
"""Jarvis Live Lot 1 — task registry and store (SPEC_JARVIS_LIVE / DEC-038).

No LLM calls: executors are monkeypatched. State goes to a tmp file and the pool
is replaced by inline execution. HTTP/SSE tests live in test_live_tasks_api.py.
"""

from __future__ import annotations

import pytest

from services import live_tasks as lt
from services.live_tasks_store import (
    STATUS_CANCELLED,
    STATUS_DONE,
    STATUS_FAILED,
    STATUS_QUEUED,
    LiveTaskStore,
)
from tests.live_tasks_fixtures import registry  # noqa: F401  (pytest fixture, redefined as test arg)

def _stub_executor(monkeypatch, text="ok", artifacts=None, exc=None):
    def fake(agent_id, instruction, session_id):
        if exc:
            raise exc
        return lt.Outcome(text=text, artifacts=artifacts or [])

    monkeypatch.setattr(lt, "_execute", fake)


# ── Registry ────────────────────────────────────────────────────────────────


def test_create_queues_and_submits(registry):
    task = lt.create_task("coo", "  Donne-moi l'état du pipeline  ", session_id="s1")
    assert task.status == STATUS_QUEUED
    assert task.instruction == "Donne-moi l'état du pipeline"
    assert registry.submitted == [task.id]
    assert registry.events[0]["status"] == STATUS_QUEUED


def test_agent_outside_allowlist_is_rejected(registry):
    with pytest.raises(ValueError, match="non autorisé"):
        lt.create_task("dev_app", "fais un truc")


def test_allowlist_follows_setting(registry, monkeypatch):
    from config.settings import get_settings

    monkeypatch.setenv("LIVE_TASK_AGENTS", "secretary")
    get_settings.cache_clear()
    try:
        assert lt.allowed_agents() == ["secretary"]
        with pytest.raises(ValueError):
            lt.create_task("coo", "x")
    finally:
        monkeypatch.delenv("LIVE_TASK_AGENTS")
        get_settings.cache_clear()


def test_empty_instruction_rejected(registry):
    with pytest.raises(ValueError):
        lt.create_task("coo", "   ")


def test_create_task_with_files_only(registry, tmp_path, monkeypatch):
    from services.hub_user_files import HubUserFileStore

    store = HubUserFileStore(
        index_path=tmp_path / "hub_files.json",
        uploads_dir=tmp_path / "hub_uploads",
    )
    monkeypatch.setattr("services.hub_user_files._store", store)
    record = store.save_bytes(b"data", "a.txt", "text/plain", source="live")
    task = lt.create_task("coo", "   ", file_ids=[record.id])
    assert task.instruction == "Voir les pièces jointes."
    assert task.file_ids == [record.id]


def test_run_task_done(registry, monkeypatch):
    _stub_executor(monkeypatch, text="Pipeline OK")
    task = lt.create_task("coo", "état pipeline")
    lt.run_task(task.id)
    done = lt.get_task(task.id)
    assert done.status == STATUS_DONE
    assert done.result == "Pipeline OK"
    assert done.started_at and done.finished_at
    assert [e["status"] for e in registry.events] == ["queued", "running", "done"]


def test_run_task_failure_is_recorded_not_raised(registry, monkeypatch):
    _stub_executor(monkeypatch, exc=RuntimeError("boom"))
    task = lt.create_task("coo", "x y")
    lt.run_task(task.id)
    failed = lt.get_task(task.id)
    assert failed.status == STATUS_FAILED
    assert "boom" in failed.error


def test_agent_claim_without_result_is_not_done(registry, monkeypatch):
    # SPEC §5.3: "j'ai fini" is not proof — an empty answer must not become `done`.
    _stub_executor(monkeypatch, text="")
    task = lt.create_task("coo", "x y")
    lt.run_task(task.id)
    assert lt.get_task(task.id).status == STATUS_FAILED
    assert lt.get_task(task.id).error == "empty_result"


def test_declared_artifact_must_exist(registry, monkeypatch, tmp_path):
    missing = str(tmp_path / "nope.md")
    _stub_executor(monkeypatch, text="fait", artifacts=[missing])
    task = lt.create_task("coo", "x y")
    lt.run_task(task.id)
    assert lt.get_task(task.id).status == STATUS_FAILED
    assert lt.get_task(task.id).error.startswith("missing_artifact")

    real = tmp_path / "ok.md"
    real.write_text("x", encoding="utf-8")
    _stub_executor(monkeypatch, text="fait", artifacts=[str(real)])
    task2 = lt.create_task("coo", "x y")
    lt.run_task(task2.id)
    assert lt.get_task(task2.id).status == STATUS_DONE


def test_cancel_queued_task_is_never_executed(registry, monkeypatch):
    calls: list[str] = []
    monkeypatch.setattr(lt, "_execute", lambda *a: calls.append("ran") or lt.Outcome(text="x"))
    task = lt.create_task("coo", "x y")
    assert lt.cancel_task(task.id).status == STATUS_CANCELLED
    lt.run_task(task.id)
    assert calls == []
    assert lt.get_task(task.id).status == STATUS_CANCELLED


def test_cancel_while_running_discards_late_result(registry, monkeypatch):
    def fake(agent_id, instruction, session_id):
        lt.cancel_task(task_id)  # user cancels while the agent is working
        return lt.Outcome(text="résultat tardif")

    monkeypatch.setattr(lt, "_execute", fake)
    task_id = lt.create_task("coo", "x y").id
    lt.run_task(task_id)
    final = lt.get_task(task_id)
    assert final.status == STATUS_CANCELLED
    assert final.result == ""


def test_finished_task_cannot_be_cancelled(registry, monkeypatch):
    _stub_executor(monkeypatch)
    task = lt.create_task("coo", "x y")
    lt.run_task(task.id)
    assert lt.cancel_task(task.id).status == STATUS_DONE
    assert lt.cancel_task("inconnu") is None


def test_plan_executor_summary(monkeypatch):
    monkeypatch.setattr(
        "services.plan_executor.run_coo_plan",
        lambda objective: {
            "title": "Veille",
            "total_steps": 2,
            "success_count": 1,
            "results": [
                {"agent_id": "analyst_data", "success": True, "result": "chiffres"},
                {"agent_id": "content", "success": False, "error": "timeout"},
            ],
        },
    )
    out = lt._run_plan("fais une veille")
    assert "1/2" in out.text and "[OK] analyst_data" in out.text and "[ÉCHEC] content" in out.text


def test_plan_with_zero_success_raises(monkeypatch):
    monkeypatch.setattr(
        "services.plan_executor.run_coo_plan",
        lambda objective: {"total_steps": 2, "success_count": 0, "results": []},
    )
    with pytest.raises(RuntimeError):
        lt._run_plan("x")


# ── Store ───────────────────────────────────────────────────────────────────


def test_restart_marks_active_tasks_failed(tmp_path):
    path = tmp_path / "t.json"
    first = LiveTaskStore(path)
    running = first.add("coo", "a b")
    first.update(running.id, status="running")
    queued = first.add("coo", "c d")
    finished = first.add("coo", "e f")
    first.update(finished.id, status=STATUS_DONE, result="ok")

    second = LiveTaskStore(path)  # simulates a Hub restart
    assert second.get(running.id).status == STATUS_FAILED
    assert second.get(running.id).error == "interrupted_by_restart"
    assert second.get(queued.id).status == STATUS_FAILED
    assert second.get(finished.id).status == STATUS_DONE


def test_corrupt_file_does_not_block_the_hub(tmp_path):
    path = tmp_path / "t.json"
    path.write_text("{ pas du json", encoding="utf-8")
    store = LiveTaskStore(path)
    assert store.list_tasks() == []
    assert store.add("coo", "a b").id
    assert (tmp_path / "t.corrupt.json").exists()


def test_store_trims_oldest_finished_only(tmp_path, monkeypatch):
    monkeypatch.setattr("services.live_tasks_store.MAX_STORED_TASKS", 3)
    store = LiveTaskStore(tmp_path / "t.json")
    ids = [store.add("coo", f"t{i}").id for i in range(3)]
    store.update(ids[0], status=STATUS_DONE)
    store.add("coo", "t3")
    remaining = {t.id for t in store.list_tasks()}
    assert ids[0] not in remaining and {ids[1], ids[2]} <= remaining




