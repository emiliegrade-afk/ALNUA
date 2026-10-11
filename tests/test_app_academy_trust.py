"""App Academy (Phase 48 engine) trust wiring — DEC-043.

Drill academies record trust in `studio_academy_engine`; the App Academy
pipeline (GitHub issue → coding pipeline → PR → merge) must feed the same
loop — otherwise dev_app can finish all 52 exercises without moving the
measured L2 gate (0.80). The conftest isolates the trust store, so these
tests exercise the real `record_validation` math end to end.
"""

from __future__ import annotations

import skills.gh_issues_process_handlers as handlers
from services import agent_trust


class _Target:
    def __init__(self, slug: str) -> None:
        self.slug = slug
        self.name = slug


def _patch_common(monkeypatch) -> None:
    monkeypatch.setattr(handlers, "set_label", lambda *a, **k: None)
    monkeypatch.setattr(handlers, "post_comment", lambda *a, **k: None)
    monkeypatch.setattr("services.coding_activity.finish_task", lambda *a, **k: None)
    monkeypatch.setattr("services.coding_learning.record_qa_failure", lambda **k: None)


def test_merge_records_trust_success(monkeypatch) -> None:
    monkeypatch.setattr("services.coding_learning.record_coding_success", lambda **k: None)
    monkeypatch.setattr("services.academy_issue_sync.close_issue", lambda *a, **k: None)
    monkeypatch.setattr(
        "services.agent_wake.queue_academy_if_idle", lambda: {"marked_count": 0}
    )

    handlers.academy_post_merge(
        42, "owner/repo", {"task_id": "t-1"}, {"pr_url": "https://x/pr/1"}, "[ACADEMY N4.2] Carte"
    )

    row = agent_trust.get_trust("dev_app")
    assert row["samples"] == 1
    assert row["successes"] == 1
    assert row["score"] > 0.7  # moved up from the 0.7 default
    hist = row["history"][0]
    assert hist["source"] == "academy:app"
    assert hist["weight"] == 0.5
    assert "N4.2" in hist["note"]


def test_failure_on_academy_records_weight_2(monkeypatch) -> None:
    _patch_common(monkeypatch)

    handlers.handle_failure(
        issue_number=7,
        title="[ACADEMY N2.3] API meteo",
        target=_Target("academy"),
        github_repo="owner/repo",
        spec={},
        result={"error": "boom"},
        activity_id="a-1",
        telegram_notify_fn=None,
    )

    row = agent_trust.get_trust("dev_app")
    assert row["failures"] == 1
    assert row["score"] < 0.7  # pulled down from the default
    hist = row["history"][0]
    assert hist["weight"] == 2.0
    assert hist["source"] == "academy:app"
    assert "N2.3" in hist["note"]


def test_failure_on_other_repo_records_nothing(monkeypatch) -> None:
    _patch_common(monkeypatch)

    handlers.handle_failure(
        issue_number=9,
        title="fix: crash on login",
        target=_Target("nuaway"),
        github_repo="owner/nuaway",
        spec={},
        result={"error": "boom"},
        activity_id="a-2",
        telegram_notify_fn=None,
    )

    row = agent_trust.get_trust("dev_app")
    assert row["samples"] == 0
    assert row["provisional"] is True
