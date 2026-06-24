"""Phase 3 — persona names aligned to CLAUDE.md / config/agent_personas.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.agent_personas import (
    get_display_name,
    persona_first_name,
    persona_prompt_intro,
)

ROOT = Path(__file__).resolve().parents[1]

LEGACY_NAMES = (
    "Aria Stern",
    "Léa Moreau",
    "Lea Moreau",
    "Marcus Webb",
    "Sven Lindqvist",
    "Kai Ito",
    "Suki Park",
    "Nova Drake",
    "Lena Rousseau",
    "Eliot Marsh",
    "Viktor Stein",
    "Rin Nakamura",
)

RUNTIME_DIRS = ("agents", "services", "api", "config")


@pytest.mark.parametrize(
    ("agent_id", "expected"),
    [
        ("coo", "Aria Voss"),
        ("pm", "Sam Rivera"),
        ("spec", "Léon Marchand"),
        ("qa", "Alex Okafor"),
        ("game_director", "Mira Chen"),
        ("dev_gaming", "Nova Fischer"),
        ("brainstorm", "Idris Okonkwo"),
        ("rnd_agent", "Alex Mercer"),
        ("marketing", "Camille Rousseau"),
        ("content", "Sofia Reyes"),
        ("hardware", "Yuki Tanaka"),
        ("embedded_dev", "Zara Singh"),
        ("secretary", "Nadia Faure"),
    ],
)
def test_canonical_display_names(agent_id: str, expected: str) -> None:
    assert get_display_name(agent_id) == expected
    assert persona_first_name(agent_id) == expected.split()[0]


def test_persona_prompt_intro_uses_canonical_name() -> None:
    intro = persona_prompt_intro("rnd_agent", role="R&D Lead")
    assert "Alex Mercer" in intro
    assert "Mira Chen" not in intro


def test_no_legacy_persona_names_in_runtime_code() -> None:
    offenders: list[str] = []
    for dirname in RUNTIME_DIRS:
        for path in (ROOT / dirname).rglob("*.py"):
            if path.name.startswith("test_"):
                continue
            text = path.read_text(encoding="utf-8")
            for legacy in LEGACY_NAMES:
                if legacy in text:
                    offenders.append(f"{path.relative_to(ROOT)}: {legacy}")
    assert not offenders, "Legacy persona names found:\n" + "\n".join(offenders)


def test_agent_system_prompts_import() -> None:
    from config.agent_operating_spec import get_system_prompt
    from config.agent_system_prompts import (
        RND_AGENT_SYSTEM_PROMPT,
        crew_backstory,
    )

    assert "Alex Mercer" in RND_AGENT_SYSTEM_PROMPT
    assert "## Mission" in RND_AGENT_SYSTEM_PROMPT
    back = crew_backstory("game_director")
    assert "Mira Chen" in back
    assert "## Processus de raisonnement" in back
    assert get_system_prompt("coo") == crew_backstory("coo")
