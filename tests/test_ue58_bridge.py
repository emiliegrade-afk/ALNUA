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


def test_gdd_sync_rejects_bad_direction() -> None:
    out = skill_ue58.gdd_sync("wyrdheim", "sideways")
    assert out["ok"] is False


def test_chat_offline(monkeypatch: Any) -> None:
    monkeypatch.delenv("UE5_SERVER_URL", raising=False)
    monkeypatch.delenv("UE58_HOST", raising=False)
    out = skill_ue58.chat("ai_programmer", "hello")
    assert out["ok"] is False
