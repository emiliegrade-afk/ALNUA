"""Tests for the academy → trust autonomy loop (DEC-043, Phase 50).

Two layers: (1) the trust store's source cap — academy successes lift at most
to ACADEMY_TRUST_CAP and never pull a higher production-earned score down;
(2) the engine wiring — validated/rejected/failed exercises record trust with
the paper-calibrated weights. No LLM calls: dispatch and QA are monkeypatched.
"""

from __future__ import annotations

import pytest

from services import agent_trust
from services import studio_academy_engine as engine_mod
from services.academy_program_analytics import ANALYTICS_PROGRAM

AN1 = "AN1.1"  # analyst_business exercise


@pytest.fixture(autouse=True)
def isolated_state(tmp_path, monkeypatch):
    monkeypatch.setattr(agent_trust, "_STORE", tmp_path / "agent_trust.json")
    monkeypatch.setenv("ALNUA_WORKSPACE", str(tmp_path / "ws"))
    monkeypatch.setenv("ANALYTICS_ACADEMY_PROGRESS_PATH", str(tmp_path / "analytics.json"))
    return tmp_path


# ---------------------------------------------------------------------------
# Trust store — source cap (DEC-043)
# ---------------------------------------------------------------------------


def test_academy_success_capped_at_085():
    for _ in range(30):
        row = agent_trust.record_validation("analyst_business", success=True, weight=0.5, source="academy:analytics")
    assert row["score"] == agent_trust.ACADEMY_TRUST_CAP
    assert row["score"] == 0.85


def test_production_source_can_exceed_cap():
    agent_trust.record_validation("analyst_business", success=True, weight=0.5, source="academy:analytics")
    for _ in range(10):
        row = agent_trust.record_validation("analyst_business", success=True, weight=2.0, source="workflow")
    assert row["score"] > agent_trust.ACADEMY_TRUST_CAP


def test_academy_success_never_lowers_production_score():
    for _ in range(10):
        agent_trust.record_validation("analyst_business", success=True, weight=2.0, source="workflow")
    before = agent_trust.get_trust("analyst_business")["score"]
    assert before > agent_trust.ACADEMY_TRUST_CAP
    row = agent_trust.record_validation("analyst_business", success=True, weight=0.5, source="academy:analytics")
    assert row["score"] == before  # unchanged, not pulled toward cap


def test_academy_failure_still_pulls_down():
    agent_trust.record_validation("analyst_business", success=True, weight=0.5, source="academy:analytics")
    capped = agent_trust.get_trust("analyst_business")["score"]
    row = agent_trust.record_validation("analyst_business", success=False, weight=1.0, source="academy:analytics")
    assert row["score"] < capped


def test_uncapped_source_has_no_cap():
    for _ in range(40):
        row = agent_trust.record_validation("content", success=True, weight=1.0, source="review_board")
    assert row["score"] > 0.95


# ---------------------------------------------------------------------------
# Engine wiring — academy outcomes feed trust
# ---------------------------------------------------------------------------


class _FakeAgent:
    def __getattr__(self, name: str):
        def _fake(**kwargs):
            return {"method": name, "summary": "livrable factice", "items": ["a", "b", "c"]}

        return _fake


def _patch_dispatch(monkeypatch, qa_verdict="validated"):
    monkeypatch.setattr(engine_mod, "_get_agent", lambda program, agent_id: _FakeAgent())
    monkeypatch.setattr(
        engine_mod,
        "_default_qa_review",
        lambda program, ex, content: {
            "verdict": qa_verdict,
            "dod_checks": [],
            "feedback": "ok" if qa_verdict == "validated" else "trop vague",
        },
    )


def _recorded(monkeypatch) -> list[dict]:
    calls: list[dict] = []
    monkeypatch.setattr(
        agent_trust,
        "record_validation",
        lambda agent_id, **kwargs: calls.append({"agent_id": agent_id, **kwargs}) or {"score": 0.77},
    )
    return calls


def test_validated_exercise_records_trust_success_paper_weight(monkeypatch):
    _patch_dispatch(monkeypatch)
    calls = _recorded(monkeypatch)
    result = engine_mod.run_exercise(ANALYTICS_PROGRAM, AN1)
    assert result["status"] == "validated"
    assert result["trust_score"] == 0.77
    assert len(calls) == 1
    assert calls[0]["agent_id"] == "analyst_business"
    assert calls[0]["success"] is True
    assert calls[0]["weight"] == 0.5
    assert calls[0]["source"] == "academy:analytics"


def test_rejected_exercise_records_failure_weight_1(monkeypatch):
    _patch_dispatch(monkeypatch, qa_verdict="rejected")
    calls = _recorded(monkeypatch)
    result = engine_mod.run_exercise(ANALYTICS_PROGRAM, AN1)
    assert result["status"] == "rejected"
    assert calls[0]["success"] is False
    assert calls[0]["weight"] == 1.0


def test_failed_after_max_attempts_records_weight_2(monkeypatch):
    _patch_dispatch(monkeypatch, qa_verdict="rejected")
    calls = _recorded(monkeypatch)
    from services.studio_academy_state import MAX_QA_ATTEMPTS

    result = {}
    for _ in range(MAX_QA_ATTEMPTS):
        result = engine_mod.run_exercise(ANALYTICS_PROGRAM, AN1)
    assert result["status"] == "failed"
    assert calls[-1]["success"] is False
    assert calls[-1]["weight"] == 2.0


def test_qa_unavailable_records_no_trust(monkeypatch):
    """QA outage is not the trainee's fault — no trust penalty (DEC-043)."""
    monkeypatch.setattr(engine_mod, "_get_agent", lambda program, agent_id: _FakeAgent())

    def _boom(program, ex, content):
        raise RuntimeError("QA down")

    monkeypatch.setattr(engine_mod, "_default_qa_review", _boom)
    calls = _recorded(monkeypatch)
    result = engine_mod.run_exercise(ANALYTICS_PROGRAM, AN1)
    assert result["status"] == "rejected"
    assert calls == []


def test_trust_scores_drive_autonomy_levels():
    from services.autonomy_resolver import trust_score_to_autonomy

    assert trust_score_to_autonomy(0.70) == 1
    assert trust_score_to_autonomy(0.84) == 2
    assert trust_score_to_autonomy(agent_trust.ACADEMY_TRUST_CAP) == 2  # academy alone: max level 2
    assert trust_score_to_autonomy(0.90) == 3
