"""Tests 9-layer agent operating specs."""

from __future__ import annotations

import pytest

from config.agent_operating_spec import get_system_prompt, list_spec_agent_ids
from config.agent_specs_registry import AGENT_OPERATING_SPECS


def test_all_core_agents_have_specs() -> None:
    core = {
        "coo",
        "secretary",
        "spec",
        "qa",
        "pm",
        "dev_app",
        "dev_backend",
        "game_director",
        "dev_gaming",
        "brainstorm",
        "rnd_agent",
        "marketing",
        "content",
        "accounting",
        "hardware",
        "embedded_dev",
        "level_designer",
        "coding_coach",
        "analyst_business",
        "analyst_data",
        "controller",
    }
    assert core <= set(AGENT_OPERATING_SPECS.keys())


def test_compile_has_nine_layers() -> None:
    prompt = get_system_prompt("rnd_agent")
    for section in (
        "## Mission",
        "## Responsabilités",
        "## Hors périmètre",
        "## Processus de raisonnement",
        "## Priorités",
        "## Communication",
        "## Mémoire",
        "## Personnalité",
        "## Format de sortie",
    ):
        assert section in prompt


def test_mission_is_single_block_not_adjectives_only() -> None:
    spec = AGENT_OPERATING_SPECS["qa"]
    assert len(spec.mission.split(".")) <= 3
    assert len(spec.processus) >= 3
    assert len(spec.hors_perimetre) >= 2


def test_secretary_out_of_scope_mentions_ceo() -> None:
    prompt = get_system_prompt("secretary")
    assert "Hors périmètre" in prompt
    assert "Emilie" in prompt


def test_unknown_agent_raises() -> None:
    with pytest.raises(KeyError):
        get_system_prompt("nonexistent_agent")


def test_list_spec_ids() -> None:
    assert len(list_spec_agent_ids()) >= 22
