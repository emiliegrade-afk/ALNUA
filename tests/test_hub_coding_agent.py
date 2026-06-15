"""Tests for Hub coding agent (tool loop, no LLM)."""

from __future__ import annotations

from pathlib import Path

from config.agent_models import CODING_AGENT_IDS, get_coding_model_for_agent
from services.hub_coding_agent import _execute_action, _safe_path


def test_coding_agents_use_unified_model_config() -> None:
    assert "dev_app" in CODING_AGENT_IDS
    assert get_coding_model_for_agent("dev_app") == get_coding_model_for_agent("dev_app_agent")


def test_safe_path_blocks_escape(tmp_path: Path) -> None:
    try:
        _safe_path(tmp_path, "../../etc/passwd")
        assert False, "should raise"
    except ValueError:
        pass


def test_write_and_read_file(tmp_path: Path) -> None:
    out = _execute_action(
        tmp_path,
        {"action": "write_file", "path": "app/x.ts", "content": "export const x = 1;\n"},
    )
    assert "OK" in out
    read = _execute_action(tmp_path, {"action": "read_file", "path": "app/x.ts"})
    assert "export const x" in read


def test_reject_empty_file(tmp_path: Path) -> None:
    out = _execute_action(
        tmp_path,
        {"action": "write_file", "path": "empty.ts", "content": ""},
    )
    assert "vide" in out.lower()
