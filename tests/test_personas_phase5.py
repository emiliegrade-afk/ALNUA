"""Phase 5 — persona naming aligned to config/agent_personas.py."""

from __future__ import annotations

from pathlib import Path

import pytest

from config.agent_personas import (
    get_display_name,
    persona_first_name,
    persona_prompt_intro,
)

ROOT = Path(__file__).resolve().parents[1]

# Legacy names retired in Phase 5 (runtime code must not reference them).
LEGACY_NAMES = (
    "Aria Stern",
    "Léa Moreau",
    "Lea Moreau",
    "Marcus Webb",
    "Sven Lindqvist",
)

RUNTIME_DIRS = ("agents", "services", "api")


@pytest.mark.parametrize(
    ("agent_id", "expected"),
    [
        ("coo", "Aria Voss"),
        ("pm", "Sam Rivera"),
        ("spec", "Léon Marchand"),
        ("qa", "Alex Okafor"),
    ],
)
def test_canonical_display_names(agent_id: str, expected: str) -> None:
    assert get_display_name(agent_id) == expected
    assert persona_first_name(agent_id) == expected.split()[0]


def test_persona_prompt_intro_uses_canonical_name() -> None:
    intro = persona_prompt_intro("coo", role="COO")
    assert "Aria Voss" in intro
    assert "Aria Stern" not in intro


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
