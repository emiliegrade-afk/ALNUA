"""Tests for services/daily_briefing.py — collectors mocked."""

from __future__ import annotations

from unittest.mock import patch

from services.daily_briefing import run_daily_briefing, run_quick_briefing


def test_run_daily_briefing_returns_coo_brief() -> None:
    fake_coo = {
        "headline": "Priorité QA",
        "priority_1": "Ship Hub",
        "priority_2": "Content",
        "priority_3": "R&D",
        "alerts": [],
        "opportunities": ["Trend AI"],
    }

    with (
        patch("services.daily_briefing._collect_leaderboard", return_value={"top_3": []}),
        patch("services.daily_briefing._collect_trends", return_value={"items": []}),
        patch("services.daily_briefing._collect_costs", return_value={"spent_usd": 1.0}),
        patch("services.daily_briefing._collect_events", return_value={"recent_count": 0}),
        patch("services.daily_briefing._collect_memory_health", return_value={"checked": 5}),
        patch("services.daily_briefing._coo_synthesize", return_value=fake_coo),
        patch("services.competition.add_points"),
    ):
        result = run_daily_briefing(context="Sprint 12")

    assert result["coo_brief"]["headline"] == "Priorité QA"
    assert "raw_data" in result
    assert result["raw_data"]["leaderboard"] == {"top_3": []}
    assert result["duration_ms"] >= 0


def test_run_quick_briefing_skips_trends() -> None:
    with (
        patch("services.daily_briefing._collect_leaderboard", return_value={}),
        patch("services.daily_briefing._collect_costs", return_value={}),
        patch("services.daily_briefing._collect_memory_health", return_value={}),
        patch(
            "services.daily_briefing._coo_synthesize",
            return_value={"headline": "Quick", "alerts": [], "opportunities": []},
        ),
        patch("services.competition.add_points"),
    ):
        result = run_quick_briefing()

    assert result["coo_brief"]["headline"] == "Quick"
    assert result["raw_data"]["trends_collected"] is False
