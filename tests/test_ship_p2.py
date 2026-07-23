"""Tests P2 — ship_game / ship_robo workflows + branch playbooks."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def workflow_runs_dir(tmp_path, monkeypatch):
    runs = tmp_path / "workflow_runs"
    runs.mkdir()
    monkeypatch.setattr("services.workflow_engine._RUNS_DIR", runs)
    return runs


def test_ship_game_recipe_registered() -> None:
    from services.workflow_engine import get_recipe

    recipe = get_recipe("ship_game")
    assert recipe is not None
    assert recipe.head_agent == "game_director"
    assert recipe.priority == "P2"
    ids = [s.id for s in recipe.steps]
    assert "validate_gaming_readiness" in ids


def test_ship_robo_recipe_registered() -> None:
    from services.workflow_engine import get_recipe

    recipe = get_recipe("ship_robo")
    assert recipe is not None
    assert recipe.head_agent == "hardware"
    ids = [s.id for s in recipe.steps]
    assert "validate_robotics_readiness" in ids


def test_validate_registry_gaming_blocks_wrong_branch() -> None:
    from services.app_registry import AppRegistryEntry
    from services.ship_readiness import validate_registry_for_branch

    entry = AppRegistryEntry(
        slug="bloc-note",
        name="Bloc note",
        branch="app",
        path_exists=True,
        local_path="C:/Dev/bloc-note",
    )
    with patch("services.app_registry.get_app", return_value=entry):
        out = validate_registry_for_branch("bloc-note", required_branch="gaming")
    assert out["status"] == "ECART"
    assert "gaming" in out["detail"]


def test_gaming_readiness_requires_gdd_or_godot(tmp_path: Path) -> None:
    from services.ship_readiness import check_gaming_readiness

    empty = check_gaming_readiness(str(tmp_path), slug="wyrd")
    assert empty["ready"] is False

    gdd_dir = tmp_path / "gaming" / "wyrd"
    gdd_dir.mkdir(parents=True)
    (gdd_dir / "gdd-extract.md").write_text(
        "# GDD\n" + "Core loop: explore, fight, loot. " * 10,
        encoding="utf-8",
    )
    ok = check_gaming_readiness(str(tmp_path), slug="wyrd")
    assert ok["ready"] is True
    assert ok.get("soft") is True


def test_robotics_readiness_hardware_brief(tmp_path: Path) -> None:
    from services.ship_readiness import check_robotics_readiness

    hw = tmp_path / "hardware" / "arm-v1"
    hw.mkdir(parents=True)
    (hw / "hardware-brief.md").write_text(
        "# BOM\n| Part | Qty |\n|------|-----|\n| MCU | 1 |\n" + "x" * 80,
        encoding="utf-8",
    )
    out = check_robotics_readiness(str(tmp_path), slug="arm-v1")
    assert out["ready"] is True


def test_ship_game_happy_path(workflow_runs_dir, tmp_path: Path) -> None:
    from services.app_registry import AppRegistryEntry
    from services.workflow_engine import run_workflow

    gdd = tmp_path / "gaming" / "wyrdheim"
    gdd.mkdir(parents=True)
    (gdd / "gdd-extract.md").write_text("# GDD\n" + "Gameplay loop defined. " * 15, encoding="utf-8")
    (tmp_path / "project.godot").write_text("[application]\nconfig/name=\"Wyrd\"", encoding="utf-8")

    mock_entry = AppRegistryEntry(
        slug="wyrdheim",
        name="Wyrdheim",
        branch="gaming",
        local_path=str(tmp_path),
        path_exists=True,
        lifecycle_status="build",
    )

    with (
        patch("services.app_registry.get_app", return_value=mock_entry),
        patch("services.app_registry.upsert_app", return_value=mock_entry),
        patch("services.company_errors.count_open_errors", return_value=0),
        patch("services.company_errors.list_open_errors", return_value=[]),
        patch("services.event_bus.emit") as emit_mock,
    ):
        result = run_workflow("ship_game", {"slug": "wyrdheim", "target_status": "beta"})

    assert result["success"] is True
    assert result["status"] == "completed"
    emit_mock.assert_called_once()


def test_gaming_playbook_override() -> None:
    from services.rnd_dispatch_playbooks import get_playbook

    pb = get_playbook("game_director", branch="gaming")
    assert pb is not None
    assert "release-gdd-checklist.md" in pb.files[0]


def test_robotics_playbook_override() -> None:
    from services.rnd_dispatch_playbooks import get_playbook

    pb = get_playbook("hardware", branch="robotics")
    assert pb is not None
    assert "release-bom-signoff.md" in pb.files[0]
