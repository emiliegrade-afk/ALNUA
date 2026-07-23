"""Tests for runtime wiring — cost tracking, event bus, learning wrapper."""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest

os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-supabase-key")
os.environ.setdefault("OPENROUTER_API_KEY", "test-openrouter-key")
os.environ.setdefault("HUB_API_KEY", "test-hub-key-for-ci")
os.environ.setdefault("ENVIRONMENT", "development")


def test_llm_client_records_usage() -> None:
    from agents.base import LLMClient

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.text = ""
    fake_response.raise_for_status = MagicMock()
    fake_response.json.return_value = {
        "choices": [{"message": {"content": "ok"}}],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
    }

    client = LLMClient()
    with (
        patch("httpx.Client") as mock_client_cls,
        patch("services.cost_monitor.record_call", return_value=0.001) as mock_record,
        patch("services.cost_monitor.check_budget_alert", return_value={"alert": False}),
        patch("skills.skill_model_usage.log_usage"),
    ):
        mock_client_cls.return_value.__enter__.return_value.post.return_value = fake_response
        out = client.chat(
            system="sys",
            messages=[{"role": "user", "content": "hi"}],
            agent_id="qa",
            method_name="test_method",
            model="anthropic/claude-haiku-4-5",
        )

    assert out == "ok"
    mock_record.assert_called_once_with(
        agent_id="qa",
        model="anthropic/claude-haiku-4-5",
        prompt_tokens=100,
        completion_tokens=50,
        method="test_method",
    )


def test_run_with_learning_emits_events() -> None:
    from agents.base import run_with_learning

    with patch("services.event_bus.emit") as mock_emit:
        result = run_with_learning("marketing", "Test task", lambda: {"ok": True})

    assert result == {"ok": True}
    mock_emit.assert_called_once()
    assert mock_emit.call_args[0][0] == "task_completed"


def test_run_with_learning_emits_on_failure() -> None:
    from agents.base import run_with_learning

    def _boom() -> None:
        raise ValueError("fail")

    with patch("services.event_bus.emit") as mock_emit:
        with pytest.raises(ValueError, match="fail"):
            run_with_learning("marketing", "Broken task", _boom)

    mock_emit.assert_called_once()
    assert mock_emit.call_args[0][0] == "task_failed"
