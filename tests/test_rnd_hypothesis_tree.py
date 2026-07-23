"""Tests Arbor-lite hypothesis tree."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def trees_dir(tmp_path, monkeypatch):
    trees = tmp_path / "rnd_trees"
    trees.mkdir()
    watch = tmp_path / "rnd_watch_topics.json"
    watch.write_text(
        json.dumps(
            {
                "topics": [
                    {
                        "id": "diffusion-gemma",
                        "title": "DiffusionGemma",
                        "summary": "Text diffusion model",
                        "tags": ["ai", "llm"],
                        "suggested_branches": ["Local Nadia ack"],
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("services.rnd_hypothesis_tree.TREES_DIR", trees)
    monkeypatch.setattr("services.rnd_hypothesis_tree.WATCH_TOPICS_FILE", watch)
    return trees


def test_start_investigation_creates_tree(trees_dir: Path) -> None:
    from services.rnd_hypothesis_tree import get_tree, start_investigation

    with patch("services.rnd_hypothesis_tree.threading.Thread") as thread_cls:
        thread_cls.return_value = MagicMock()
        result = start_investigation("robotique", requested_by="test")

    assert result["success"] is True
    assert result["slug"]
    tree = get_tree(result["slug"])
    assert tree is not None
    assert tree["topic"] == "robotique"
    assert len(tree["nodes"]) == 1
    assert tree["nodes"][0]["status"] == "pending"
    thread_cls.assert_called_once()


def test_match_watch_topics_diffusion(trees_dir: Path) -> None:
    from services.rnd_hypothesis_tree import _match_watch_topics

    hits = _match_watch_topics("recherche DiffusionGemma pour agents locaux")
    assert any(h.get("id") == "diffusion-gemma" for h in hits)


def test_ideate_includes_watch_branches(trees_dir: Path) -> None:
    from services.rnd_hypothesis_tree import _ideate_branches

    tree = {
        "topic": "modèles IA locaux",
        "nodes": {
            "root": {
                "id": "root",
                "title": "Root",
                "hypothesis": "Explorer IA locale",
                "status": "explored",
                "insight": "Latence importante",
            }
        },
    }
    parent = tree["nodes"]["root"]

    with patch("agents.base.LLMClient") as llm_cls:
        llm = MagicMock()
        llm.complete.return_value = json.dumps(
            {
                "branches": [
                    {"title": "DiffusionGemma Nadia", "hypothesis": "Ack ultra-rapide"},
                ]
            }
        )
        llm_cls.return_value = llm
        branches = _ideate_branches("modèles IA locaux", parent, tree, max_count=2)

    assert branches
    assert "DiffusionGemma" in branches[0]["title"] or "Nadia" in branches[0]["title"]


def test_list_trees(trees_dir: Path) -> None:
    from services.rnd_hypothesis_tree import list_trees, start_investigation

    with patch("services.rnd_hypothesis_tree.threading.Thread"):
        start_investigation("gaming VR", requested_by="test")

    trees = list_trees()
    assert len(trees) == 1
    assert trees[0]["topic"] == "gaming VR"
