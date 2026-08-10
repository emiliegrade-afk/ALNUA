"""Phase A isolation — locks, slots, merge policy (DEC-022)."""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest

from services.execution_slots import (
    SlotBusyError,
    acquire_slot,
    get_limits,
    release_slot,
    reset_slots_for_tests,
    slot_status,
)
from services.merge_policy import (
    MergeDeniedError,
    assert_can_merge,
    can_merge,
    is_protected_branch,
)
from services.resource_locks import (
    LockBusyError,
    acquire,
    get_lock,
    list_locks,
    make_key,
    release,
    release_all,
    reset_store_for_tests,
)


@pytest.fixture(autouse=True)
def _clean_isolation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    store = tmp_path / "resource_locks.json"
    monkeypatch.setattr("services.resource_locks._STORE", store)
    reset_store_for_tests(store)
    reset_slots_for_tests()
    monkeypatch.setenv("HUB_API_KEY", "test-hub-key-for-ci")
    monkeypatch.setenv("ISOLATION_ENABLED", "1")
    monkeypatch.setenv("ISOLATION_MAX_GLOBAL", "8")
    monkeypatch.setenv("ISOLATION_MAX_PER_REPO", "2")
    monkeypatch.setenv("ISOLATION_MAX_PER_AGENT", "1")
    monkeypatch.setenv("ISOLATION_WAIT_S", "0")
    monkeypatch.setenv("ISOLATION_INTEGRATOR_ONLY_MERGE", "1")
    monkeypatch.setenv("ISOLATION_FIX_PIPELINE_MERGE", "1")
    monkeypatch.setenv("CODING_AUTO_MERGE", "false")
    try:
        from config.settings import get_settings

        get_settings.cache_clear()
    except Exception:
        pass
    yield
    reset_slots_for_tests()
    reset_store_for_tests(store)
    try:
        from config.settings import get_settings

        get_settings.cache_clear()
    except Exception:
        pass


def test_make_key_normalizes_paths() -> None:
    assert make_key("path", "web\\src\\a.ts") == "path:web/src/a.ts"


def test_lock_exclusive_same_path() -> None:
    acquire("path:web/a.ts", holder_id="h1", agent_id="dev_app", wait_s=0)
    with pytest.raises(LockBusyError):
        acquire("path:web/a.ts", holder_id="h2", agent_id="dev_frontend", wait_s=0)
    assert release("path:web/a.ts", "h1") is True
    acquire("path:web/a.ts", holder_id="h2", agent_id="dev_frontend", wait_s=0)
    release_all("h2")


def test_lock_same_holder_reentrant() -> None:
    a = acquire("ticket:42", holder_id="h1", agent_id="dev_app", wait_s=0)
    b = acquire("ticket:42", holder_id="h1", agent_id="dev_app", wait_s=0)
    assert a["lease_id"] == b["lease_id"] or a["holder_id"] == b["holder_id"]
    release_all("h1")


def test_disjoint_paths_parallel() -> None:
    acquire("path:a.py", holder_id="h1", agent_id="dev_backend", wait_s=0)
    acquire("path:b.py", holder_id="h2", agent_id="dev_frontend", wait_s=0)
    assert len(list_locks()) == 2
    release_all("h1")
    release_all("h2")


def test_lock_wait_then_acquire() -> None:
    acquire("ticket:wait", holder_id="h1", agent_id="dev_app", wait_s=0)

    def _release_later() -> None:
        time.sleep(0.15)
        release("ticket:wait", "h1")

    threading.Thread(target=_release_later, daemon=True).start()
    row = acquire("ticket:wait", holder_id="h2", agent_id="dev_frontend", wait_s=2.0, poll_s=0.05)
    assert row["holder_id"] == "h2"
    release_all("h2")


def test_slot_per_agent_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "services.execution_slots.get_limits",
        lambda: type("L", (), {"max_global": 8, "max_per_repo": 4, "max_per_agent": 1})(),
    )
    t1 = acquire_slot(agent_id="dev_app", holder_id="h1", repo_key="hub", wait_s=0)
    with pytest.raises(SlotBusyError):
        acquire_slot(agent_id="dev_app", holder_id="h2", repo_key="hub", wait_s=0)
    release_slot(t1)
    t2 = acquire_slot(agent_id="dev_app", holder_id="h2", repo_key="hub", wait_s=0)
    release_slot(t2)


def test_slot_per_repo_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "services.execution_slots.get_limits",
        lambda: type("L", (), {"max_global": 8, "max_per_repo": 1, "max_per_agent": 4})(),
    )
    t1 = acquire_slot(agent_id="dev_app", holder_id="h1", repo_key="hub", wait_s=0)
    with pytest.raises(SlotBusyError):
        acquire_slot(agent_id="dev_frontend", holder_id="h2", repo_key="hub", wait_s=0)
    release_slot(t1)


def test_coding_isolation_collision(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.agent_isolation import coding_isolation

    monkeypatch.setattr("services.agent_isolation._wait_s", lambda: 0.0)
    monkeypatch.setattr("services.agent_isolation.isolation_enabled", lambda: True)
    monkeypatch.setattr(
        "services.execution_slots.get_limits",
        lambda: type("L", (), {"max_global": 8, "max_per_repo": 4, "max_per_agent": 4})(),
    )

    spec_a = {
        "agent_id": "dev_app",
        "task_id": "T-1",
        "repo_path": "C:/Dev/ALUNA_HUB",
        "repo_slug": "hub",
        "files_to_modify": ["web/src/page.tsx"],
        "title": "A",
    }
    spec_b = {
        "agent_id": "dev_frontend",
        "task_id": "T-2",
        "repo_path": "C:/Dev/ALUNA_HUB",
        "repo_slug": "hub",
        "files_to_modify": ["web/src/page.tsx"],
        "title": "B",
    }
    with coding_isolation(spec_a) as lease_a:
        assert lease_a is not None
        assert get_lock("path:web/src/page.tsx") is not None
        with pytest.raises(LockBusyError):
            with coding_isolation(spec_b):
                pass


def test_coding_isolation_disjoint_files(monkeypatch: pytest.MonkeyPatch) -> None:
    from services.agent_isolation import coding_isolation

    monkeypatch.setattr("services.agent_isolation._wait_s", lambda: 0.0)
    monkeypatch.setattr("services.agent_isolation.isolation_enabled", lambda: True)
    monkeypatch.setattr(
        "services.execution_slots.get_limits",
        lambda: type("L", (), {"max_global": 8, "max_per_repo": 4, "max_per_agent": 4})(),
    )

    with coding_isolation(
        {
            "agent_id": "dev_backend",
            "task_id": "T-a",
            "repo_slug": "hub",
            "files_to_modify": ["api/main.py"],
        }
    ):
        with coding_isolation(
            {
                "agent_id": "dev_frontend",
                "task_id": "T-b",
                "repo_slug": "hub",
                "files_to_modify": ["web/src/x.tsx"],
            }
        ) as lease_b:
            assert lease_b is not None
            assert len(list_locks()) >= 2


def test_merge_policy_integrator_only() -> None:
    assert is_protected_branch("main")
    ok, reason = can_merge("dev_integrator", "main")
    assert ok and reason == "dev_integrator"
    ok, reason = can_merge("dev_app", "main")
    assert not ok
    with pytest.raises(MergeDeniedError):
        assert_can_merge("dev_app", "staging")


def test_merge_policy_fix_pipeline_and_academy() -> None:
    ok, _ = can_merge("fix_pipeline", "main")
    assert ok
    ok, reason = can_merge("coding_pipeline", "main", repo_slug="academy")
    assert ok and reason == "academy_auto_merge"
    ok, reason = can_merge("coding_pipeline", "main", repo_slug="hub")
    assert not ok


def test_slot_status_shape() -> None:
    t = acquire_slot(agent_id="qa", holder_id="h", repo_key="hub", wait_s=0)
    status = slot_status()
    assert status["active"] == 1
    assert "limits" in status
    release_slot(t)
    assert get_limits().max_per_agent >= 1
