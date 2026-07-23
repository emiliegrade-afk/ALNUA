"""Tests diversité R&D + Nadia desktop."""

from __future__ import annotations

from unittest.mock import patch

from agents.rnd_center import (
    build_rnd_diversity_block,
    count_recent_vanlife_ideas,
    get_vision,
)
from services.nadia_desktop import build_boot_greeting, register_pc_boot


def test_get_vision_not_vanlife_only():
    # Mem0 recall is environment-dependent; test the hardcoded base vision.
    with patch("skills.skill_mem0.recall", return_value=""):
        vision = get_vision()
    assert "vanlife" in vision.lower() or "NUAWAY" in vision
    assert "gaming" in vision.lower() or "robotique" in vision.lower()
    assert "max" in vision.lower() or "diversif" in vision.lower()


def test_count_recent_vanlife_ideas():
    ideas = [
        {"title": "App spots vanlife offline", "description": "camping", "created_at": "2026-06-17"},
        {"title": "Robot Eve assistant", "description": "hardware", "created_at": "2026-06-16"},
    ]
    assert count_recent_vanlife_ideas(ideas) == 1


def test_build_rnd_diversity_block_warns_when_biased():
    ideas = [
        {"title": f"Van app {i}", "description": "nomad camping", "created_at": f"2026-06-{10+i}"}
        for i in range(5)
    ]
    block = build_rnd_diversity_block([], ideas)
    assert "ALERTE" in block or "vanlife" in block.lower()
    assert "QUOTAS" in block


def test_nadia_boot_greeting():
    online = build_boot_greeting(hub_online=True)
    offline = build_boot_greeting(hub_online=False)
    assert "Nadia" in online
    assert "Hub" in offline or "hub" in offline.lower()


def test_register_pc_boot(tmp_path, monkeypatch):
    import services.nadia_desktop as mod

    monkeypatch.setattr(mod, "_STATE_PATH", tmp_path / "nadia.json")
    monkeypatch.setattr(mod, "probe_hub", lambda: {"online": True, "api_url": "http://127.0.0.1:8003"})
    monkeypatch.setattr(
        "agents.base.log_agent_action",
        lambda *a, **k: None,
    )
    monkeypatch.setattr(
        "database.supabase_client.get_supabase",
        lambda: None,
    )

    result = register_pc_boot(source="test")
    assert result["boot_count"] == 1
    assert "greeting" in result
