"""Tests ALNUA Workflow Engine — Hermes-lite recipes."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def workflow_runs_dir(tmp_path, monkeypatch):
    runs = tmp_path / "workflow_runs"
    runs.mkdir()
    monkeypatch.setattr("services.workflow_engine._RUNS_DIR", runs)
    return runs


def test_list_recipes_includes_p0() -> None:
    from services.workflow_engine import list_recipes

    ids = {r["id"] for r in list_recipes()}
    assert "dossier_ceo" in ids
    assert "ship_app" in ids
    assert "run_ops" in ids


def test_run_unknown_recipe() -> None:
    from services.workflow_engine import run_workflow

    result = run_workflow("nonexistent")
    assert result["success"] is False
    assert "inconnue" in result["error"]


def test_ship_app_blocks_missing_slug(workflow_runs_dir: Path) -> None:
    from services.workflow_engine import run_workflow

    result = run_workflow("ship_app", {"slug": ""})
    assert result["blocked"] is True
    assert result["blocked_at_step"] == "validate_registry"
    assert (workflow_runs_dir / f"{result['run_id']}.json").exists()


def test_ship_app_happy_path(workflow_runs_dir: Path) -> None:
    from services.app_registry import AppRegistryEntry
    from services.workflow_engine import run_workflow

    mock_entry = AppRegistryEntry(
        slug="testapp",
        name="Test App",
        branch="app",
        local_path="C:/Dev/testapp",
        path_exists=True,
        lifecycle_status="build",
    )

    with (
        patch("services.app_registry.get_app", return_value=mock_entry),
        patch("services.app_registry.upsert_app", return_value=mock_entry),
        patch("services.coding_error_journal.count_open_errors", return_value=0),
        patch("services.coding_error_journal.list_open_errors", return_value=[]),
        patch("services.event_bus.emit") as emit_mock,
    ):
        result = run_workflow(
            "ship_app",
            {"slug": "testapp", "target_status": "beta"},
        )

    assert result["success"] is True
    assert result["status"] == "completed"
    emit_mock.assert_called_once()


def test_run_ops_scan_registry(workflow_runs_dir: Path) -> None:
    from services.app_registry import AppRegistryEntry
    from services.workflow_engine import run_workflow

    apps = [
        AppRegistryEntry(slug="a1", name="A1", branch="app", path_exists=True),
        AppRegistryEntry(slug="hub", name="Hub", branch="hub", path_exists=True),
    ]

    with (
        patch("services.app_registry.list_apps", return_value=apps),
        patch("services.coding_error_journal.count_open_errors", return_value=0),
        patch("services.coding_error_journal.list_open_errors", return_value=[]),
        patch(
            "services.run_watchdog_registry.build_watchdog_coverage_report",
            return_value={"summary": "ok", "unmapped_slugs": []},
        ),
    ):
        result = run_workflow("run_ops", {})

    assert result["success"] is True
    scan = next(s for s in result["steps"] if s["step_id"] == "scan_registry")
    assert scan["status"] == "OK"
    assert scan["result"]["apps"][0]["slug"] == "a1"


def test_dossier_ceo_blocks_no_dossier(workflow_runs_dir: Path) -> None:
    from services.workflow_engine import run_workflow

    with patch("services.rnd_repository.get_rnd_repository") as repo_cls:
        repo = MagicMock()
        repo.get_dossier.return_value = None
        repo_cls.return_value = repo
        result = run_workflow("dossier_ceo", {"dossier_id": "missing"})

    assert result["blocked"] is True
    assert result["blocked_at_step"] == "validate_sections"


def test_coding_error_journal_open_filters() -> None:
    from services.coding_error_journal import count_open_errors, list_open_errors

    journal = {
        "version": 1,
        "entries": [
            {"id": "1", "status": "open", "repo_slug": "academy", "created_at": "2026-01-02"},
            {"id": "2", "status": "open", "repo_slug": "hub", "created_at": "2026-01-03"},
            {"id": "3", "status": "resolved", "repo_slug": "academy", "created_at": "2026-01-01"},
        ],
        "patterns": {},
    }

    with patch("services.coding_error_journal.load_journal", return_value=journal):
        assert count_open_errors(repo_slug="academy") == 1
        assert len(list_open_errors(repo_slug="academy")) == 1


def test_watchdog_coverage_report() -> None:
    from services.app_registry import AppRegistryEntry
    from services.run_watchdog_registry import build_watchdog_coverage_report

    apps = [
        AppRegistryEntry(slug="academy", name="Academy", branch="app", local_path="C:/Dev/alnua-academy", path_exists=True),
        AppRegistryEntry(slug="ghost", name="Ghost", branch="app", path_exists=False),
    ]

    with (
        patch("services.app_registry.list_apps", return_value=apps),
        patch("services.coding_error_journal.count_open_errors", return_value=0),
        patch(
            "services.run_watchdog_registry.resolve_repo_path_for_slug",
            return_value=("C:/Dev/alnua-academy", "org/academy"),
        ),
    ):
        report = build_watchdog_coverage_report()

    assert "ghost" in report["unmapped_slugs"]
    assert len(report["mapped"]) == 1
