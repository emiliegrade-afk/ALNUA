"""Vague A — UE5.8 bridge (DEC-017): honest offline + capability filter."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from agents.ai_programmer_agent import AiProgrammerAgent
from agents.technical_artist_agent import TechnicalArtistAgent
from agents.vfx_artist_agent import VfxArtistAgent
from skills import skill_ue58


def test_ue58_not_configured(monkeypatch: Any) -> None:
    monkeypatch.delenv("UE5_SERVER_URL", raising=False)
    monkeypatch.delenv("UE58_HOST", raising=False)
    out = skill_ue58.ue58_health()
    assert out["ok"] is False
    assert out["configured"] is False
    assert out["connected"] is False
    assert "UE5" in out["error"] or "UE58" in out["error"] or "configur" in out["error"].lower()


def test_ue58_configured_but_down(monkeypatch: Any) -> None:
    monkeypatch.setenv("UE5_SERVER_URL", "http://127.0.0.1:59999")
    with patch.object(skill_ue58, "_get", side_effect=ConnectionError("down")):
        out = skill_ue58.ue58_health()
    assert out["configured"] is True
    assert out["connected"] is False
    assert out["ok"] is False


def test_probe_filters_ai_programmer_caps(monkeypatch: Any) -> None:
    monkeypatch.setenv("UE5_SERVER_URL", "http://127.0.0.1:8765")
    caps = [
        {"id": "bt_create_tree", "category": "behavior", "description": "BT"},
        {"id": "render_stat", "category": "render", "description": "FPS"},
        {"id": "niagara_spawn", "category": "niagara", "description": "FX"},
    ]
    with (
        patch.object(
            skill_ue58,
            "ue58_health",
            return_value={"ok": True, "configured": True, "connected": True, "server": {}},
        ),
        patch.object(skill_ue58, "list_capabilities", return_value=caps),
    ):
        out = AiProgrammerAgent().probe_ue58()
    assert out["ok"] is True
    assert out["capabilities_total"] == 3
    ids = {c["id"] for c in out["capabilities"]}
    assert "bt_create_tree" in ids
    assert "render_stat" not in ids


def test_probe_technical_and_vfx_filters(monkeypatch: Any) -> None:
    monkeypatch.setenv("UE5_SERVER_URL", "http://127.0.0.1:8765")
    caps = [
        {"id": "bt_create_tree", "category": "behavior", "description": "BT"},
        {"id": "render_stat", "category": "render", "description": "FPS"},
        {"id": "niagara_spawn", "category": "niagara", "description": "FX"},
    ]
    with (
        patch.object(
            skill_ue58,
            "ue58_health",
            return_value={"ok": True, "configured": True, "connected": True},
        ),
        patch.object(skill_ue58, "list_capabilities", return_value=caps),
    ):
        tech = TechnicalArtistAgent().probe_ue58()
        vfx = VfxArtistAgent().probe_ue58()
    assert {c["id"] for c in tech["capabilities"]} == {"render_stat"}
    assert {c["id"] for c in vfx["capabilities"]} == {"niagara_spawn"}


def test_probe_phase21_remaining_agents(monkeypatch: Any) -> None:
    """Vague A suite — environment / narrative / sound / qa_gaming filters."""
    from agents.environment_artist_agent import EnvironmentArtistAgent
    from agents.narrative_designer_agent import NarrativeDesignerAgent
    from agents.qa_gaming_agent import QaGamingAgent
    from agents.sound_designer_agent import SoundDesignerAgent

    monkeypatch.setenv("UE5_SERVER_URL", "http://127.0.0.1:8765")
    caps = [
        {"id": "landscape_sculpt", "category": "landscape", "description": "env"},
        {"id": "dialogue_cue", "category": "dialogue", "description": "lines"},
        {"id": "meta_sound_play", "category": "audio", "description": "sfx"},
        {"id": "pie_start", "category": "pie", "description": "qa"},
        {"id": "bt_create_tree", "category": "behavior", "description": "BT"},
    ]
    with (
        patch.object(
            skill_ue58,
            "ue58_health",
            return_value={"ok": True, "configured": True, "connected": True},
        ),
        patch.object(skill_ue58, "list_capabilities", return_value=caps),
    ):
        env = EnvironmentArtistAgent().probe_ue58()
        narr = NarrativeDesignerAgent().probe_ue58()
        snd = SoundDesignerAgent().probe_ue58()
        qa = QaGamingAgent().probe_ue58()
    assert {c["id"] for c in env["capabilities"]} == {"landscape_sculpt"}
    assert {c["id"] for c in narr["capabilities"]} == {"dialogue_cue"}
    assert {c["id"] for c in snd["capabilities"]} == {"meta_sound_play"}
    assert {c["id"] for c in qa["capabilities"]} == {"pie_start"}


def test_narrative_canon_search_uses_lore(monkeypatch: Any) -> None:
    from agents.narrative_designer_agent import NarrativeDesignerAgent

    monkeypatch.setattr(
        "skills.skill_lore_database.search_lore",
        lambda query, project=None, limit=5: [{"title": "Yggdrasil", "snippet": query}],
    )
    out = NarrativeDesignerAgent().search_canon("arbre monde", game="Wyrdheim")
    assert out["ok"] is True
    assert out["count"] == 1


def test_qa_gaming_builds_degrades(monkeypatch: Any) -> None:
    from agents.qa_gaming_agent import QaGamingAgent

    monkeypatch.setattr(
        "database.supabase_client.get_supabase",
        lambda: (_ for _ in ()).throw(RuntimeError("no db")),
    )
    out = QaGamingAgent().list_recent_builds(limit=3)
    assert out["ok"] is False
    assert out["builds"] == []


def test_gdd_sync_rejects_bad_direction() -> None:
    out = skill_ue58.gdd_sync("wyrdheim", "sideways")
    assert out["ok"] is False


def test_chat_offline(monkeypatch: Any) -> None:
    monkeypatch.delenv("UE5_SERVER_URL", raising=False)
    monkeypatch.delenv("UE58_HOST", raising=False)
    out = skill_ue58.chat("ai_programmer", "hello")
    assert out["ok"] is False
