"""Tests for services/app_registry.py."""

from __future__ import annotations

import json

import pytest


@pytest.fixture
def registry_file(tmp_path, monkeypatch):
    path = tmp_path / "apps_registry.json"
    path.write_text(json.dumps({"apps": []}), encoding="utf-8")
    import services.app_registry as mod

    monkeypatch.setattr(mod, "_REGISTRY_PATH", path)
    return path


def test_upsert_and_list(registry_file, monkeypatch):
    import services.app_registry as mod
    from services.app_registry import AppRegistryUpsert, get_app, list_apps, upsert_app

    monkeypatch.setattr(mod, "get_repo_targets", lambda: ())

    upsert_app(
        AppRegistryUpsert(
            slug="demo-app",
            name="Demo App",
            branch="app",
            local_path="C:/Dev/demo",
            github_repo="org/demo",
            stack="Next.js",
        )
    )
    entry = get_app("demo-app")
    assert entry is not None
    assert entry.name == "Demo App"
    assert entry.github_configured is True

    raw = json.loads(registry_file.read_text(encoding="utf-8"))
    assert len(raw["apps"]) == 1

    apps = list_apps()
    assert any(a.slug == "demo-app" for a in apps)
