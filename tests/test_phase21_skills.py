"""Phase 21 — 3 useful skill hooks (Nwiro / Pi / BOM) without silent stubs."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from agents.ai_programmer_agent import AiProgrammerAgent
from agents.electronics_agent import ElectronicsAgent
from agents.firmware_agent import FirmwareAgent
from skills import skill_bom, skill_nwiro, skill_pi_ssh


def test_nwiro_probe_offline() -> None:
    with patch.object(skill_nwiro, "nwiro_is_available", return_value=False):
        out = AiProgrammerAgent().probe_nwiro_tools()
    assert out["ok"] is False
    assert out["connected"] is False
    assert "UE5" in out["error"] or "Nwiro" in out["error"]


def test_nwiro_probe_lists_bt_tools() -> None:
    tools = [
        {"name": "bt_create_tree", "description": "Create BT"},
        {"name": "blueprint_create", "description": "BP"},
    ]
    with (
        patch.object(skill_nwiro, "nwiro_is_available", return_value=True),
        patch.object(skill_nwiro, "nwiro_list_tools", return_value=tools),
    ):
        out = AiProgrammerAgent().probe_nwiro_tools()
    assert out["ok"] is True
    assert out["tools_total"] == 2
    assert len(out["bt_tools"]) == 1


def test_pi_probe_not_configured() -> None:
    with patch.object(skill_pi_ssh, "pi_is_configured", return_value=False):
        out = FirmwareAgent().probe_pi("uname -a")
    assert out["ok"] is False
    assert out["configured"] is False


def test_pi_denylist_blocks_rm_rf() -> None:
    with (
        patch.object(skill_pi_ssh, "pi_is_configured", return_value=True),
        patch.dict("os.environ", {"PI_HOST": "192.168.1.10"}, clear=False),
    ):
        out = skill_pi_ssh.run_pi_command("rm -rf /")
    assert out["success"] is False
    assert "bloqu" in out["output"].lower() or "block" in out["output"].lower()


def test_bom_context_ok(monkeypatch: Any) -> None:
    monkeypatch.setattr(
        skill_bom,
        "list_bom_items",
        lambda: [{"id": "1", "component": "IMU", "category": "vision", "quantity": 1, "status": "a_commander"}],
    )
    # get_bom_context imports list_bom_items from eve_bom at call time via skill_bom
    monkeypatch.setattr(
        "services.eve_bom.list_bom_items",
        lambda db=None: [
            {
                "id": "1",
                "component": "IMU",
                "category": "vision",
                "quantity": 1,
                "status": "a_commander",
            }
        ],
    )
    out = ElectronicsAgent().bom_context(category="vision")
    assert out["ok"] is True
    assert out["items"][0]["component"] == "IMU"


def test_review_board_llm_flag_off(monkeypatch: Any) -> None:
    from services.review_board_llm import llm_debate_enabled, run_optional_debate

    monkeypatch.delenv("REVIEW_BOARD_LLM", raising=False)
    assert llm_debate_enabled() is False
    assert (
        run_optional_debate(
            department="app",
            artifact={"title": "x"},
            gate={"score": 0.9, "threshold": 0.7, "checks": []},
            reviewers=None,
        )
        is None
    )
