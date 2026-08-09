"""Vague B Phase 21 — robotics lab/BOM/Pi probes (honest offline)."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from agents.industrial_design_agent import IndustrialDesignAgent
from agents.mechanical_agent import MechanicalAgent
from agents.qa_robot_agent import QaRobotAgent
from agents.safety_agent import SafetyAgent
from agents.simulation_agent import SimulationAgent
from agents.vision_ai_agent import VisionAiAgent
from skills import skill_bom, skill_pi_ssh, skill_robo_lab


def test_mechanical_and_industrial_bom(monkeypatch: Any) -> None:
    rows = [
        {
            "id": "1",
            "component": "Chassis plate",
            "category": "structure",
            "quantity": 1,
            "status": "a_commander",
        }
    ]
    monkeypatch.setattr(skill_bom, "list_bom_items", lambda: rows)
    mech = MechanicalAgent().bom_context(category="structure")
    ind = IndustrialDesignAgent().bom_context(category="structure")
    assert mech["ok"] is True
    assert ind["ok"] is True
    assert mech["items"][0]["component"] == "Chassis plate"


def test_qa_lab_empty() -> None:
    with patch.object(
        skill_robo_lab,
        "get_lab_context",
        return_value={"ok": True, "count": 0, "items": [], "empty": True, "message": "vide"},
    ):
        out = QaRobotAgent().lab_context()
    assert out["ok"] is True
    assert out["empty"] is True


def test_safety_lab_bundle_unavailable() -> None:
    with patch.object(
        skill_robo_lab,
        "get_lab_bundle",
        return_value={"ok": False, "error": "Lab tests indisponibles: down", "lab": {}, "builds": {}},
    ):
        out = SafetyAgent().lab_context()
    assert out["ok"] is False
    assert "indisponible" in (out.get("error") or "").lower()


def test_vision_pi_not_configured() -> None:
    with patch.object(skill_pi_ssh, "pi_is_configured", return_value=False):
        out = VisionAiAgent().probe_pi("uname -a")
    assert out["ok"] is False
    assert out["configured"] is False


def test_simulation_lab_context(monkeypatch: Any) -> None:
    with (
        patch.object(
            skill_robo_lab,
            "get_lab_bundle",
            return_value={"ok": True, "lab": {"items": []}, "builds": {"items": []}},
        ),
        patch.object(
            skill_bom,
            "get_bom_context",
            return_value={"ok": True, "items": [], "count": 0},
        ),
    ):
        out = SimulationAgent().lab_context()
    assert out["ok"] is True
    assert "lab_bundle" in out
    assert "bom" in out


def test_lab_context_db_error() -> None:
    with patch(
        "database.supabase_client.get_supabase",
        side_effect=RuntimeError("no db"),
    ):
        out = skill_robo_lab.get_lab_context()
    assert out["ok"] is False
    assert out["items"] == []
