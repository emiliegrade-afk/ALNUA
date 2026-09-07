"""Phase 35 Depth+ — Brand voice debate Élise ↔ Anouk."""
from __future__ import annotations

from typing import Any


def test_debate_falls_back_structural_when_llm_fails(monkeypatch: Any) -> None:
    from services import brand_voice_debate as bvd

    monkeypatch.setattr(
        bvd,
        "_run_elise_anouk",
        lambda *a, **k: None,
    )
    out = bvd.debate_brand_voice(
        "ALNUA builds agents in public — honest progress, no corporate slop.",
        department="marketing",
    )
    assert out["deliberated"] is False
    assert out["mode"] == "structural_only"
    assert out["structural"]["ok"] is True
    assert out["recommendation"] == "approve"


def test_debate_merges_verdicts(monkeypatch: Any) -> None:
    from services import brand_voice_debate as bvd

    monkeypatch.setattr(
        bvd,
        "_run_elise_anouk",
        lambda *a, **k: {
            "rounds": [
                {
                    "round": 1,
                    "agent": "brand",
                    "name": "Élise",
                    "payload": {"stance": "approve", "summary": "OK visuelle"},
                },
                {
                    "round": 1,
                    "agent": "content_company",
                    "name": "Anouk",
                    "payload": {"stance": "approve", "summary": "OK voix"},
                },
            ],
            "consensus": {
                "verdict": "approve",
                "elise": "OK visuelle",
                "anouk": "OK voix",
                "dissent": [],
                "actions": ["Publier"],
            },
        },
    )
    out = bvd.debate_brand_voice(
        "ALNUA builds agents in public — honest progress, no corporate slop.",
        department="marketing",
        rounds=1,
    )
    assert out["deliberated"] is True
    assert out["mode"] == "elise_anouk"
    assert out["ok"] is True
    assert out["recommendation"] == "approve"
    assert out["debate"]["verdict"] == "approve"


def test_debate_revise_when_structural_fails(monkeypatch: Any) -> None:
    from services import brand_voice_debate as bvd

    monkeypatch.setattr(
        bvd,
        "_run_elise_anouk",
        lambda *a, **k: {
            "rounds": [],
            "consensus": {
                "verdict": "approve",
                "elise": "ok",
                "anouk": "ok",
                "dissent": [],
                "actions": [],
            },
        },
    )
    out = bvd.debate_brand_voice("hi", department="app")
    assert out["ok"] is False
    assert out["recommendation"] == "revise"
