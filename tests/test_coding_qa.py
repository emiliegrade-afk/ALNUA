"""Tests for services/coding_qa.py."""

from __future__ import annotations

from pathlib import Path

from services.coding_qa import _check_empty_or_junk_files, run_pre_pr_qa
from services.coding_pipeline import get_coding_config, should_auto_merge_repo


def test_academy_auto_merge_enabled_by_default() -> None:
    cfg = get_coding_config()
    assert should_auto_merge_repo("academy", cfg) is True
    assert should_auto_merge_repo("hub", cfg) is False


def test_empty_file_detected(tmp_path: Path) -> None:
    import subprocess

    (tmp_path / "README.md").write_text("ok", encoding="utf-8")
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.email", "t@test.com"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "checkout", "-b", "feat"], cwd=tmp_path, capture_output=True)
    (tmp_path / "app").mkdir()
    (tmp_path / "app" / "login.tsx").write_text("", encoding="utf-8")
    subprocess.run(["git", "add", "app/login.tsx"], cwd=tmp_path, capture_output=True)
    subprocess.run(["git", "commit", "-m", "empty login"], cwd=tmp_path, capture_output=True)
    errors = _check_empty_or_junk_files(tmp_path, "master")
    assert any("vide" in e for e in errors)


def test_qa_skipped_when_disabled(monkeypatch) -> None:
    monkeypatch.setenv("CODING_QA_REQUIRED", "false")
    get_coding_config.cache_clear()
    qa = run_pre_pr_qa("/tmp", {"repo_slug": "academy"}, "master")
    get_coding_config.cache_clear()
    assert qa["passed"] is True
