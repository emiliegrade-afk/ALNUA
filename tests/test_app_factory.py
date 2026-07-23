"""Tests App Factory — Phase 2."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from services.app_factory import (
    FactoryTask,
    _fallback_plan,
    _slugify,
    ensure_local_scaffold,
    format_issue_body,
    generate_factory_plan,
    register_factory_app,
    start_app_factory_run,
)


def test_slugify():
    assert _slugify("Mon Super App!") == "mon-super-app"


def test_fallback_plan_nextjs():
    tasks = _fallback_plan("Demo", "Une app de test", "nextjs")
    assert len(tasks) >= 2
    assert "Next" in tasks[0].title or "scaffold" in tasks[0].title.lower()


def test_format_issue_body_parsed_sections():
    task = FactoryTask(
        title="Scaffold",
        description="Init project",
        files_to_create=["src/app/page.tsx"],
        tests_to_pass=["npm run build"],
    )
    body = format_issue_body(task, "nextjs")
    assert "## Description" in body
    assert "## Stack" in body
    assert "nextjs" in body
    assert "src/app/page.tsx" in body


def test_generate_factory_plan_dry_run():
    tasks = generate_factory_plan("X", "Brief long enough for test", "nextjs", dry_run=True)
    assert len(tasks) >= 1


def test_ensure_local_scaffold(tmp_path: Path):
    target = tmp_path / "new-app"
    created = ensure_local_scaffold("new-app", "nextjs", target)
    assert created is True
    assert (target / "README.md").exists()
    assert (target / "package.json").exists()


def test_start_factory_run():
    from services.app_factory import AppFactoryRequest

    queued = start_app_factory_run(
        AppFactoryRequest(name="Test", brief="Brief minimum viable"),
        dry_run=True,
    )
    assert queued["run_id"]
    assert queued["status"] == "queued"


@pytest.fixture
def registry_file(tmp_path, monkeypatch):
    path = tmp_path / "apps_registry.json"
    path.write_text(json.dumps({"apps": []}), encoding="utf-8")
    import services.app_registry as mod

    monkeypatch.setattr(mod, "_REGISTRY_PATH", path)
    return path


def test_register_factory_app(registry_file, monkeypatch):
    import services.app_registry as mod
    from services.app_factory import AppFactoryRequest

    monkeypatch.setattr(mod, "get_repo_targets", lambda: ())
    req = AppFactoryRequest(
        name="Ma App",
        brief="Description détaillée du produit",
        stack="nextjs",
        github_repo="org/ma-app",
        local_path="C:/Dev/ma-app",
    )
    entry = register_factory_app(req, "ma-app")
    assert entry["slug"] == "ma-app"
    assert entry["github_repo"] == "org/ma-app"
