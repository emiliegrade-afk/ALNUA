"""Tests for PRD → GitHub issues (Phase 3)."""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest

from services.engineering_spec import EngineeringTask
from services.prd_issues import (
    format_issue_body,
    github_title,
    publish_tasks_to_github,
    resolve_repo_slug_for_dossier,
)
from services.rnd_schemas import RndDossierOut


def _dossier() -> RndDossierOut:
    return RndDossierOut(
        id="d-1",
        idea_id="i-1",
        slug="nuaway",
        title="NUAWAY Beta",
        domain="app",
    )


def test_resolve_repo_slug_nomad(monkeypatch):
    monkeypatch.setenv("GITHUB_REPO_NOMAD", "org/nomad")
    from config.github_repos import get_repo_targets

    get_repo_targets.cache_clear()
    slug = resolve_repo_slug_for_dossier(_dossier())
    assert slug == "nomad"
    get_repo_targets.cache_clear()


def test_github_title_prefix():
    task = EngineeringTask(id="T-1", title="Add map screen")
    title = github_title(task, dossier_slug="nuaway")
    assert title.startswith("[AGENT]")
    assert "nuaway" in title


def test_format_issue_body_agent_task_sections():
    task = EngineeringTask(
        id="T-001",
        title="Auth flow",
        description="Implement Supabase auth",
        stack="react_native_expo",
        files_create=["app/login.tsx"],
        files_modify=["app/_layout.tsx"],
        tests=["__tests__/auth.test.tsx"],
        priority="P0",
        sprint=1,
    )
    body = format_issue_body(task, dossier_slug="nuaway", dossier_title="NUAWAY")
    assert "## Description" in body
    assert "## Stack" in body
    assert "react_native_expo" in body
    assert "app/login.tsx" in body


@patch("services.prd_issues.create_github_issue")
@patch("services.prd_issues.list_existing_titles")
@patch("services.prd_issues.write_deliverable")
@patch("services.prd_issues.init_build_manifest")
@patch("services.prd_issues.update_build_manifest_issues")
def test_publish_tasks_dry_run(
    mock_update_manifest,
    mock_init_manifest,
    mock_write,
    mock_list_titles,
    mock_create,
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv("GITHUB_REPO_NOMAD", "org/nomad")
    monkeypatch.setenv("ALNUA_WORKSPACE", str(tmp_path))
    from config.github_repos import get_repo_targets

    get_repo_targets.cache_clear()

    mock_list_titles.return_value = set()
    mock_init_manifest.return_value = {}
    mock_update_manifest.return_value = {"issues_created": 1}

    tasks = [
        EngineeringTask(id="T-001", title="Setup", priority="P0", sprint=1),
        EngineeringTask(id="T-002", title="Map", priority="P1", sprint=1),
    ]
    result = publish_tasks_to_github(_dossier(), tasks, dry_run=True, mark_ready_count=1)
    assert result["dry_run"] is True
    assert result["created_count"] == 2
    mock_create.assert_not_called()
    get_repo_targets.cache_clear()


@patch("services.prd_issues.create_github_issue")
@patch("services.prd_issues.list_existing_titles")
@patch("services.prd_issues.write_deliverable")
@patch("services.prd_issues.init_build_manifest")
@patch("services.prd_issues.update_build_manifest_issues")
def test_publish_tasks_idempotent_skip(
    mock_update_manifest,
    mock_init_manifest,
    mock_write,
    mock_list_titles,
    mock_create,
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv("GITHUB_REPO_NOMAD", "org/nomad")
    monkeypatch.setenv("ALNUA_WORKSPACE", str(tmp_path))
    from config.github_repos import get_repo_targets

    get_repo_targets.cache_clear()

    task = EngineeringTask(id="T-001", title="Setup", priority="P0", sprint=1)
    existing_title = github_title(task, dossier_slug="nuaway")
    mock_list_titles.return_value = {existing_title}
    mock_init_manifest.return_value = {}
    mock_update_manifest.return_value = {}

    result = publish_tasks_to_github(_dossier(), [task], dry_run=False)
    assert result["skipped_count"] == 1
    assert result["created_count"] == 0
    mock_create.assert_not_called()
    get_repo_targets.cache_clear()
