"""AgentBase.run_json_task — shared one-shot JSON path for specialty agents."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agents.agent_base import AgentBase


def test_run_json_task_returns_parsed_dict(monkeypatch: pytest.MonkeyPatch) -> None:
    agent = AgentBase.__new__(AgentBase)
    agent.AGENT_NAME = "test_agent"
    agent.db = MagicMock()

    monkeypatch.setattr(agent, "_complete", lambda *a, **k: '{"ok": true}')
    monkeypatch.setattr(
        "skills.skill_agent_learning.inject_learning_context",
        lambda prompt, *_a, **_k: prompt,
    )
    monkeypatch.setattr(
        "skills.skill_agent_learning.record_task_learning",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        "agents.agent_base.log_agent_action",
        lambda *_a, **_k: {},
    )

    result = agent.run_json_task(
        action="ping",
        prompt="return ok",
        learning_key="k",
        input_summary="in",
        output_summary="out",
    )
    assert result == {"ok": True}
