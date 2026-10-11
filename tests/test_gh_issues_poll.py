"""Per-repo serialization of the issue polling loop (BUG-032).

Two coding pipelines on the SAME repo collide on shared files (LockBusyError)
and double the API-process CPU burst. The poll loop now serializes per repo
slug while keeping cross-repo parallelism bounded by the global semaphore.
"""

from __future__ import annotations

import asyncio
import threading
import time

import pytest

import skills.gh_issues_poll as poll


@pytest.fixture(autouse=True)
def _fresh_semaphores(monkeypatch: pytest.MonkeyPatch):
    """Semaphores bind to the running loop — reset them per test."""
    monkeypatch.setattr(poll, "_issue_semaphore", None)
    poll._repo_semaphores.clear()
    monkeypatch.setenv("CODING_MAX_PARALLEL", "2")
    yield
    poll._repo_semaphores.clear()


def test_same_repo_issues_are_serialized(monkeypatch: pytest.MonkeyPatch) -> None:
    order: list[str] = []
    first_started = threading.Event()
    allow_first_finish = threading.Event()

    def fake_process(issue, repo_path, notify) -> None:
        n = issue["number"]
        order.append(f"start:{n}")
        if n == 1:
            first_started.set()
            allow_first_finish.wait(5)
        order.append(f"end:{n}")

    monkeypatch.setattr(poll, "process_issue", fake_process)

    async def main() -> None:
        t1 = asyncio.create_task(
            poll._process_issue_bounded({"number": 1, "_repo_slug": "academy"}, None)
        )
        await asyncio.to_thread(first_started.wait, 5)
        t2 = asyncio.create_task(
            poll._process_issue_bounded({"number": 2, "_repo_slug": "academy"}, None)
        )
        await asyncio.sleep(0.3)  # give t2 every chance to start if parallel
        assert order == ["start:1"], "second same-repo issue must wait for the first"
        allow_first_finish.set()
        await asyncio.gather(t1, t2)

    asyncio.run(main())
    assert order == ["start:1", "end:1", "start:2", "end:2"]


def test_different_repos_run_in_parallel(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    def fake_process(issue, repo_path, notify) -> None:
        events.append(f"start:{issue['number']}")
        time.sleep(0.15)
        events.append(f"end:{issue['number']}")

    monkeypatch.setattr(poll, "process_issue", fake_process)

    async def main() -> None:
        await asyncio.gather(
            poll._process_issue_bounded({"number": 1, "_repo_slug": "academy"}, None),
            poll._process_issue_bounded({"number": 2, "_repo_slug": "naia"}, None),
        )

    asyncio.run(main())
    # Overlap proof: the second repo's start precedes the first repo's end.
    assert events.index("start:2") < events.index("end:1")


def test_crash_releases_repo_semaphore(monkeypatch: pytest.MonkeyPatch) -> None:
    order: list[str] = []

    def fake_process(issue, repo_path, notify) -> None:
        n = issue["number"]
        order.append(f"start:{n}")
        if n == 1:
            raise RuntimeError("boom")
        order.append(f"end:{n}")

    monkeypatch.setattr(poll, "process_issue", fake_process)

    async def main() -> None:
        await poll._process_issue_bounded({"number": 1, "_repo_slug": "academy"}, None)
        await poll._process_issue_bounded({"number": 2, "_repo_slug": "academy"}, None)

    asyncio.run(main())  # must not deadlock after the crash
    assert order == ["start:1", "start:2", "end:2"]
