"""Tests automation tool operating specs."""

from __future__ import annotations

import pytest

from config.agent_operating_spec import get_system_prompt, list_spec_agent_ids
from config.tool_specs_registry import TOOL_OPERATING_SPECS


@pytest.mark.parametrize("spec_id", list(TOOL_OPERATING_SPECS.keys()))
def test_tool_spec_registered(spec_id: str) -> None:
    assert spec_id in list_spec_agent_ids()
    prompt = get_system_prompt(spec_id)
    assert "## Mission" in prompt
    assert "## Hors périmètre" in prompt


def test_fix_pipeline_uses_registry_prompts() -> None:
    assert "## Mission" in get_system_prompt("fix_pipeline_qa_review")
    assert "## Mission" in get_system_prompt("fix_pipeline_spec_review")


def test_skill_code_agent_spec_format() -> None:
    prompt = get_system_prompt("code_agent_bug_fix")
    assert "===SUMMARY===" in prompt


def test_hub_coding_agent_system() -> None:
    from services.hub_coding_agent import _SYSTEM

    assert "## Processus de raisonnement" in _SYSTEM
    assert "done" in _SYSTEM.lower()
