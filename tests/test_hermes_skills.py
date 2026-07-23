"""Tests for Hermes skills loader (local clone at C:\\Dev\\hermes-agent-main)."""

from pathlib import Path

import pytest

from services import hermes_skills as hs


@pytest.fixture
def hermes_root():
    root = Path(r"C:\Dev\hermes-agent-main\skills")
    if not root.is_dir():
        pytest.skip("Hermes clone not at C:\\Dev\\hermes-agent-main\\skills")
    return root


def test_catalog_lists_bundled_skills(hermes_root, monkeypatch):
    monkeypatch.setattr(hs, "get_hermes_skills_root", lambda: hermes_root)
    hs.load_skill_body.cache_clear()
    cat = hs.list_catalog()
    assert cat["available"] is True
    assert len(cat["skills"]) >= 5


def test_load_github_pr_workflow(hermes_root, monkeypatch):
    monkeypatch.setattr(hs, "get_hermes_skills_root", lambda: hermes_root)
    hs.load_skill_body.cache_clear()
    body = hs.load_skill_body("github/github-pr-workflow")
    assert body
    assert "Pull Request" in body or "PR" in body


def test_inject_bundle_truncates(monkeypatch, hermes_root):
    monkeypatch.setattr(hs, "get_hermes_skills_root", lambda: hermes_root)
    hs.load_skill_body.cache_clear()
    text = hs.load_skills_for_bundle("coding", max_chars=500)
    assert "Hermes" in text or "skill" in text.lower()
    assert len(text) <= 650
