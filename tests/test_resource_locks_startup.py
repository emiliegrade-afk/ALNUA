"""Startup reap of zombie pipeline locks (BUG-032).

Lock holders are threads of the API process — after a restart, persisted
coding/fix locks belong to dead threads and would block retried pipelines
for up to the 1h TTL. The startup sweep releases them while preserving any
non-pipeline holder.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from services.resource_locks import (
    acquire,
    get_lock,
    make_key,
    release_process_locks_for_startup,
    reset_store_for_tests,
)


@pytest.fixture(autouse=True)
def _isolated_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    store = tmp_path / "resource_locks.json"
    monkeypatch.setattr("services.resource_locks._STORE", store)
    reset_store_for_tests(store)
    yield store
    reset_store_for_tests(store)


def test_startup_reaps_coding_and_fix_locks() -> None:
    acquire(
        make_key("task", "GH-academy-79"),
        holder_id="coding:dev_app:GH-academy-79",
        agent_id="dev_app",
        ttl_s=3600,
    )
    acquire(
        make_key("path", "app/(tabs)/_layout.tsx"),
        holder_id="coding:dev_app:GH-academy-79",
        agent_id="dev_app",
        ttl_s=3600,
    )
    acquire(
        make_key("task", "f7287f11"),
        holder_id="fix:f7287f11",
        agent_id="dev_app",
        ttl_s=3600,
    )

    reaped = release_process_locks_for_startup()

    assert reaped == 3
    assert get_lock(make_key("task", "GH-academy-79")) is None
    assert get_lock(make_key("path", "app/(tabs)/_layout.tsx")) is None
    assert get_lock(make_key("task", "f7287f11")) is None


def test_startup_preserves_non_pipeline_holders() -> None:
    acquire(
        make_key("task", "lounge-session-1"),
        holder_id="lounge:dev_gaming:session-1",
        agent_id="dev_gaming",
        ttl_s=3600,
    )
    acquire(
        make_key("task", "GH-academy-80"),
        holder_id="coding:dev_app:GH-academy-80",
        agent_id="dev_app",
        ttl_s=3600,
    )

    reaped = release_process_locks_for_startup()

    assert reaped == 1
    assert get_lock(make_key("task", "lounge-session-1")) is not None


def test_startup_reap_on_empty_store() -> None:
    assert release_process_locks_for_startup() == 0
