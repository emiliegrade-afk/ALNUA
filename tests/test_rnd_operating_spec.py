"""Tests R&D pipeline operating specs (9-layer model)."""

from __future__ import annotations

import pytest

from config.agent_operating_spec import (
    build_committee_system_prompt,
    get_system_prompt,
    list_spec_agent_ids,
)
from config.rnd_specs_registry import RND_OPERATING_SPECS


@pytest.mark.parametrize(
    "spec_id",
    [
        "rnd_library_expand",
        "rnd_competitor_pain",
        "rnd_idea_generator",
        "rnd_idea_evaluator",
        "rnd_mini_spec",
        "rnd_dossier_section_draft",
        "rnd_dossier_section_revise",
        "rnd_committee_overlay",
        "rnd_ceo_package",
        "rnd_social_strategy",
        "rnd_social_post",
    ],
)
def test_rnd_spec_has_nine_layers(spec_id: str) -> None:
    prompt = get_system_prompt(spec_id)
    for section in (
        "## Mission",
        "## Responsabilités",
        "## Hors périmètre",
        "## Processus de raisonnement",
        "## Priorités",
        "## Personnalité",
        "## Format de sortie",
    ):
        assert section in prompt


def test_rnd_specs_merged_in_registry() -> None:
    for key in RND_OPERATING_SPECS:
        assert key in list_spec_agent_ids()


def test_committee_prompt_layers_member_and_overlay() -> None:
    prompt = build_committee_system_prompt("pm", "Titre : Test dossier")
    assert "Sam Rivera" in prompt
    assert "## Mission" in prompt
    assert "## Mode comité R&D" in prompt
    assert "≤120 mots" in prompt or "120 mots" in prompt
    assert "Test dossier" in prompt


def test_dossier_prompts_use_registry() -> None:
    from agents.rnd_dossier_prompts import REVISE_SECTION_SYSTEM, SECTION_DRAFT_SYSTEM

    assert "## Hors périmètre" in SECTION_DRAFT_SYSTEM
    assert "anti-fluff" in SECTION_DRAFT_SYSTEM.lower() or "ANTI-FLUFF" in SECTION_DRAFT_SYSTEM
    assert REVISE_SECTION_SYSTEM.startswith("Tu es")


def test_social_prompts_use_registry() -> None:
    from agents.rnd_social_prompts import SOCIAL_POST_SYSTEM, SOCIAL_STRATEGY_SYSTEM

    assert "build in public" in SOCIAL_POST_SYSTEM.lower() or "build-in-public" in SOCIAL_POST_SYSTEM.lower()
    assert "## Objectif" in SOCIAL_STRATEGY_SYSTEM or "Objectif" in SOCIAL_STRATEGY_SYSTEM
