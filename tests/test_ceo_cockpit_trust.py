"""Tests for the CEO cockpit trust section (DEC-043, Phase 50 suite).

The cockpit must expose per-agent trust (score, autonomy level, distance to
the next band) with silent degradation — same contract as the other sections.
"""

from __future__ import annotations

from services import agent_trust
from services.ceo_cockpit import _next_threshold, get_ceo_cockpit


def test_trust_section_empty_store():
    cockpit = get_ceo_cockpit()
    trust = cockpit["trust"]
    assert trust["agents"] == []
    assert trust["count"] == 0
    assert trust["academy_cap"] == agent_trust.ACADEMY_TRUST_CAP


def test_trust_section_lists_agents_sorted_with_levels():
    agent_trust.record_validation("analyst_business", success=True, weight=0.5, source="academy:analytics", note="AN1.1 validated")
    agent_trust.record_validation("analyst_data", success=False, weight=1.0, source="academy:analytics", note="AN1.2 rejected")

    cockpit = get_ceo_cockpit()
    agents = {a["agent_id"]: a for a in cockpit["trust"]["agents"]}

    layla = agents["analyst_business"]
    assert layla["score"] > 0.70
    assert layla["autonomy_level"] == 1
    assert layla["samples"] == 1
    assert layla["next_threshold"] == 0.80
    assert layla["last_note"] == "AN1.1 validated"

    axel = agents["analyst_data"]
    assert axel["score"] < 0.70
    assert axel["autonomy_level"] == 0
    assert axel["failures"] == 1

    # Sorted by score desc — Layla (success) before Axel (failure).
    ids = [a["agent_id"] for a in cockpit["trust"]["agents"]]
    assert ids.index("analyst_business") < ids.index("analyst_data")


def test_next_threshold_bands():
    assert _next_threshold(0.65) == 0.70
    assert _next_threshold(0.75) == 0.80
    assert _next_threshold(0.85) == 0.90
    assert _next_threshold(0.95) is None
