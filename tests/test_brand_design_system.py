"""Phase 35 / Vague D — design system + brand seat on Review Board."""
from __future__ import annotations

from typing import Any

import pytest


def test_get_design_system_defaults(monkeypatch: Any) -> None:
    from services import brand_design_system as bds

    monkeypatch.setattr(bds, "_latest_kit_analysis", lambda: (None, None))
    ds = bds.get_design_system()
    assert ds["ok"] is True
    assert ds["source"]["colors"] == "hub_defaults"
    assert len(ds["color_tokens"]) >= 3
    assert "tone" in ds["voice"]
    assert "brand" in ds["reviewers"]
    assert "layout_tokens" in ds
    assert ds["layout_tokens"]["radius_md"] == "12px"


def test_get_design_system_kit_guidelines(monkeypatch: Any) -> None:
    from services import brand_design_system as bds

    analysis = {
        "style": "Minimal dark luxury",
        "mood": ["confident", "warm"],
        "usage_notes": "Copper accent on obsidian only.",
        "colors": [{"hex": "#E09B6A", "role": "accent", "name": "Copper"}],
    }
    monkeypatch.setattr(bds, "_latest_kit_analysis", lambda: (analysis, "kit_abc"))
    ds = bds.get_design_system()
    assert ds["source"]["colors"] == "brand_kit"
    assert any("Kit mood" in g for g in ds["guidelines"])
    assert any("Kit style" in g for g in ds["guidelines"])
    assert ds["kit_meta"]["mood"] == ["confident", "warm"]


def test_brand_persona_registered() -> None:
    from config.agent_personas import AGENT_PERSONAS, get_persona

    assert "brand" in AGENT_PERSONAS
    persona = get_persona("brand")
    assert persona is not None
    assert persona["room"] == "comms_hub"
    assert persona["team"] == "business"
    assert persona["competitive"] is True
    assert get_persona("brand_agent") == persona


def test_review_flags_forbidden_and_thin() -> None:
    from services.brand_design_system import review_brand_coherence

    thin = review_brand_coherence("hi", department="app")
    assert thin["ok"] is False
    assert any(f.startswith("too_thin") for f in thin["flags"])

    slop = review_brand_coherence(
        "We will revolutionize the market with synergy",
        department="content",
    )
    assert slop["ok"] is False
    assert any("forbidden_word" in f for f in slop["flags"])

    good = review_brand_coherence(
        "ALNUA builds agents in public — honest progress, no corporate slop.",
        department="marketing",
    )
    assert good["ok"] is True
    assert good["recommendation"] == "approve"


def test_review_board_brand_seat_blocks_slop(trust_store: Any) -> None:
    from services.review_board import evaluate_submission

    result = evaluate_submission(
        department="marketing",
        artifact={
            "title": "Launch",
            "body": "We will disrupt and revolutionize everything today.",
            "status": "ready",
        },
        producer_agent_id="marketing",
        record_trust=False,
    )
    assert "brand" in result["reviewers"]
    assert result["gate_open"] is False
    assert result["recommendation"] == "revise"
    assert result.get("brand_review") is not None
    assert any(
        c.get("id") == "brand_coherence" and c.get("ok") is False
        for c in result["checks"]
    )


def test_resolve_reviewers_recipes() -> None:
    from config.review_board_recipes import resolve_reviewers

    assert "brand" in resolve_reviewers("content")
    assert resolve_reviewers("app", ["qa"]) == ["qa"]


@pytest.fixture
def trust_store(tmp_path: Any, monkeypatch: Any) -> Any:
    path = tmp_path / "agent_trust.json"
    monkeypatch.setattr("services.agent_trust._STORE", path)
    return path
