"""reset_stuck_in_pipeline — zombie in-pipeline recovery (BUG-030).

A completed pipeline (success OR failure) always removes in-pipeline, so an
old label means the hub died mid-run. Without a reset path, busy slots leak
permanently and the App Academy stalls on pipeline_full (seen 2026-10-11:
12 zombies, 0 slots, 15h silent).
"""

from __future__ import annotations

from types import SimpleNamespace

import services.agent_wake_queue as wake_queue
from services.agent_wake_queue import reset_stuck_in_pipeline

_OLD = "2026-10-10T02:00:00Z"  # > 24h before now
_FRESH = "2099-01-01T00:00:00Z"  # far future — always inside the window


class _Resp:
    def __init__(self, payload):
        self._p = payload

    def raise_for_status(self) -> None:
        return None

    def json(self):
        return self._p


class _FakeClient:
    """Minimal httpx.Client stand-in: serves canned issues, records PATCHes."""

    issues: list[dict] = []

    def __init__(self) -> None:
        self.patches: list[dict] = []

    def __enter__(self) -> "_FakeClient":
        _FakeClient.last = self
        return self

    def __exit__(self, *args) -> bool:
        return False

    def get(self, url, headers=None, params=None) -> _Resp:
        return _Resp(_FakeClient.issues)

    def patch(self, url, headers=None, json=None) -> _Resp:
        self.patches.append({"url": url, "json": json})
        return _Resp({})


def _issue(number: int, *, updated: str, labels: list[str], title: str = "[ACADEMY N4.1] X") -> dict:
    return {
        "number": number,
        "title": title,
        "state": "open",
        "updated_at": updated,
        "labels": [{"name": lbl} for lbl in labels],
    }


def _setup(monkeypatch, issues: list[dict]) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "test-token")
    monkeypatch.setattr(
        wake_queue,
        "get_target_by_slug",
        lambda slug: SimpleNamespace(github_repo="owner/academy", slug="academy"),
    )
    monkeypatch.setattr(wake_queue.httpx, "Client", _FakeClient)
    _FakeClient.issues = issues


def test_old_in_pipeline_reset_to_ready(monkeypatch) -> None:
    _setup(monkeypatch, [_issue(65, updated=_OLD, labels=["academy", "level-4", "in-pipeline"])])

    result = reset_stuck_in_pipeline()

    assert result["reset_count"] == 1
    assert result["reset"][0]["number"] == 65
    patch = _FakeClient.last.patches[0]
    assert patch["url"].endswith("/issues/65")
    assert "in-pipeline" not in patch["json"]["labels"]
    assert "agent-ready" in patch["json"]["labels"]


def test_existing_agent_ready_label_preserved(monkeypatch) -> None:
    _setup(monkeypatch, [_issue(71, updated=_OLD, labels=["in-pipeline", "agent-ready"])])

    result = reset_stuck_in_pipeline()

    assert result["reset_count"] == 1
    labels = _FakeClient.last.patches[0]["json"]["labels"]
    assert labels.count("agent-ready") == 1  # not duplicated


def test_fresh_in_pipeline_untouched(monkeypatch) -> None:
    _setup(monkeypatch, [_issue(80, updated=_FRESH, labels=["in-pipeline"])])

    result = reset_stuck_in_pipeline()

    assert result["reset_count"] == 0
    assert not _FakeClient.last.patches


def test_pull_requests_and_foreign_titles_skipped(monkeypatch) -> None:
    _setup(
        monkeypatch,
        [
            {**_issue(90, updated=_OLD, labels=["in-pipeline"]), "pull_request": {"url": "x"}},
            _issue(91, updated=_OLD, labels=["in-pipeline"], title="fix: unrelated bug"),
        ],
    )

    result = reset_stuck_in_pipeline()

    assert result["reset_count"] == 0
    assert not _FakeClient.last.patches


def test_unconfigured_target_returns_zero(monkeypatch) -> None:
    monkeypatch.setattr(wake_queue, "get_target_by_slug", lambda slug: None)

    assert reset_stuck_in_pipeline() == {"reset_count": 0, "reset": []}


def test_wake_agents_runs_reset_before_queue(monkeypatch) -> None:
    import services.agent_wake as agent_wake

    calls: list[str] = []
    monkeypatch.setattr("services.academy_issue_sync.run_academy_sync", lambda: {"ok": True})
    monkeypatch.setattr(agent_wake, "requeue_failed_academy", lambda count=1: {"retried_count": 0})

    def _fake_reset():
        calls.append("reset")
        return {"reset_count": 2, "reset": [{"number": 65}, {"number": 71}]}

    def _fake_queue(**kwargs):
        calls.append("queue")
        return {"marked_count": 0}

    monkeypatch.setattr(agent_wake, "reset_stuck_in_pipeline", _fake_reset)
    monkeypatch.setattr(agent_wake, "queue_academy_if_idle", _fake_queue)
    monkeypatch.setattr(
        agent_wake,
        "get_pipeline_status",
        lambda: {"verdict": "working", "message": "ok", "academy": {}},
    )

    result = agent_wake.wake_agents(sync=True, retry_failed=True)

    assert calls == ["reset", "queue"]  # slots freed before queueing
    assert {"reset_stuck_in_pipeline": {"reset_count": 2, "reset": [{"number": 65}, {"number": 71}]}} in result[
        "actions"
    ]
