"""Tests for OpenRouter prompt caching + retry caps."""

from __future__ import annotations

from unittest.mock import MagicMock, patch


def test_apply_prompt_cache_adds_session_and_top_level() -> None:
    from services.openrouter_prompt_cache import apply_prompt_cache_to_payload

    payload = {
        "model": "deepseek/deepseek-chat-v3.1",
        "messages": [
            {"role": "system", "content": "You are a coding agent."},
            {"role": "user", "content": "fix bug"},
        ],
    }
    out = apply_prompt_cache_to_payload(
        payload, model="deepseek/deepseek-chat-v3.1", agent_id="dev_app"
    )
    assert out["session_id"] == "alnua:dev_app"
    assert out["cache_control"]["type"] == "ephemeral"
    assert out["cache_control"].get("ttl") == "1h"
    # DeepSeek is automatic — system stays plain string
    assert isinstance(out["messages"][0]["content"], str)


def test_explicit_cache_control_for_anthropic() -> None:
    from services.openrouter_prompt_cache import build_system_message

    msg = build_system_message(
        "STATIC SYSTEM PROMPT " * 50,
        model="anthropic/claude-sonnet-4",
        ttl="1h",
        enable=True,
    )
    assert msg["role"] == "system"
    assert isinstance(msg["content"], list)
    assert msg["content"][0]["cache_control"]["type"] == "ephemeral"
    assert msg["content"][0]["cache_control"]["ttl"] == "1h"


def test_cost_monitor_applies_cache_discount() -> None:
    from services.cost_monitor import _compute_cost

    full = _compute_cost("default", 10_000, 0, cached_tokens=0)
    cached = _compute_cost("default", 10_000, 0, cached_tokens=10_000)
    assert cached < full
    assert abs(cached - full * 0.1) < 1e-9


def test_llm_client_payload_includes_prompt_cache() -> None:
    from agents.base import LLMClient

    fake_response = MagicMock()
    fake_response.status_code = 200
    fake_response.text = ""
    fake_response.json.return_value = {
        "choices": [{"message": {"content": "ok"}}],
        "usage": {
            "prompt_tokens": 5000,
            "completion_tokens": 10,
            "prompt_tokens_details": {"cached_tokens": 4800},
            "cost": 0.001,
        },
    }

    client = LLMClient()
    with (
        patch("httpx.Client") as mock_client_cls,
        patch("services.cost_monitor.record_call", return_value=0.001) as mock_record,
        patch("services.cost_monitor.check_budget_alert", return_value={"alert": False}),
        patch("skills.skill_model_usage.log_usage"),
    ):
        mock_post = mock_client_cls.return_value.__enter__.return_value.post
        mock_post.return_value = fake_response
        out = client.chat(
            system="sys " * 200,
            messages=[{"role": "user", "content": "hi"}],
            agent_id="dev_app",
            method_name="test",
            model="minimax/minimax-m3",
            use_cache=False,
        )

    assert out == "ok"
    sent = mock_post.call_args.kwargs["json"]
    assert sent["session_id"] == "alnua:dev_app"
    assert sent["cache_control"]["type"] == "ephemeral"
    mock_record.assert_called_once()
    assert mock_record.call_args.kwargs.get("cached_tokens") == 4800
    assert mock_record.call_args.kwargs.get("native_cost_usd") == 0.001


def test_retry_loop_skips_mcp_auth_burns() -> None:
    from skills.skill_retry_loop import classify_error, _effective_max_attempts

    class Boom(Exception):
        pass

    err = Boom("MCP tool schema unavailable")
    assert classify_error(err) == "MCPError"
    assert _effective_max_attempts("MCPError", 3) == 1
    assert _effective_max_attempts("TimeoutError", 3) == 3
