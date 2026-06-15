"""Simplified a_b_tester tests."""

from __future__ import annotations

from unittest.mock import patch

from services.a_b_tester import ABTestConfig, RunResult, quick_compare, run_ab_test


def _fake_run(variant_dict, label, runs):
    return [
        RunResult(
            variant=label,
            agent_id=variant_dict.get("agent_id", ""),
            method=variant_dict.get("method", ""),
            result={"text": label},
            cost_ms=10,
            success=True,
        )
    ]


def test_quick_compare_returns_winner() -> None:
    fake_judgment = {
        "winner": "A",
        "confidence": 0.9,
        "reasoning": "A is clearer",
        "score_a": 8.0,
        "score_b": 6.0,
    }

    with (
        patch("services.a_b_tester._run_variant", side_effect=_fake_run),
        patch("services.a_b_tester._judge_results", return_value=fake_judgment),
        patch("services.competition.add_points"),
    ):
        out = quick_compare(
            agent_id="qa",
            method="handle_instruction",
            kwargs_a={"instruction": "a"},
            kwargs_b={"instruction": "b"},
        )

    assert out["winner"] == "A"
    assert out["judge_reasoning"] == "A is clearer"


def test_run_ab_test_tie_on_judge_failure() -> None:
    config = ABTestConfig(
        name="test",
        variant_a={"agent_id": "qa", "method": "m", "kwargs": {}},
        variant_b={"agent_id": "qa", "method": "m", "kwargs": {"x": 1}},
    )

    with (
        patch("services.a_b_tester._run_variant", side_effect=_fake_run),
        patch(
            "services.a_b_tester._judge_results",
            return_value={"winner": "tie", "confidence": 0.0, "reasoning": "fail"},
        ),
        patch("services.competition.add_points"),
    ):
        out = run_ab_test(config)

    assert out["winner"] == "tie"
