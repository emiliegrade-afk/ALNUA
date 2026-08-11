"""Tests — contract templates registry + legal counsel wiring."""

from __future__ import annotations

from config.contract_templates_registry import (
    list_contract_templates,
    resolve_template,
    template_prompt_block,
)
from config.agent_operating_spec import get_system_prompt


def test_templates_list_non_empty():
    items = list_contract_templates()
    ids = {t["id"] for t in items}
    assert "nda" in ids
    assert "influenceur" in ids
    assert "pub" in ids
    assert "freelance" not in ids  # alias hidden


def test_freelance_aliases_prestation():
    meta = resolve_template("freelance")
    assert meta is not None
    assert meta["id"] == "prestation"


def test_template_prompt_block():
    block = template_prompt_block("influenceur")
    assert "Influenceur" in block or "influenceur" in block.lower()
    assert "articles" in block.lower() or "1." in block


def test_legal_counsel_system_prompt():
    prompt = get_system_prompt("legal_counsel")
    assert "juridique" in prompt.lower() or "entreprise" in prompt.lower()
