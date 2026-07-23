"""Phase 2 — hypothesis tree graph, expand, promote, benchmark."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def trees_dir(tmp_path, monkeypatch):
    trees = tmp_path / "rnd_trees"
    trees.mkdir()
    bench = tmp_path / "rnd_llm_benchmarks.json"
    bench.write_text('{"runs": []}', encoding="utf-8")
    monkeypatch.setattr("services.rnd_hypothesis_tree.TREES_DIR", trees)
    monkeypatch.setattr("services.rnd_llm_benchmark.BENCHMARK_FILE", bench)
    return trees


def _seed_tree(trees_dir, monkeypatch) -> str:
    from services.rnd_hypothesis_tree import start_investigation

    with patch("services.rnd_hypothesis_tree.threading.Thread"):
        result = start_investigation("robotique", requested_by="test")
    return result["slug"]


def test_build_tree_graph_layout(trees_dir, monkeypatch) -> None:
    slug = _seed_tree(trees_dir, monkeypatch)
    from services.rnd_hypothesis_tree import build_tree_graph, expand_node

    tree = json.loads((trees_dir / f"{slug}.json").read_text(encoding="utf-8"))
    root_id = tree["root_id"]

    with patch("services.rnd_hypothesis_tree._ideate_branches") as ideate:
        ideate.return_value = [
            {"title": "B2B", "hypothesis": "Marché B2B"},
            {"title": "Hardware", "hypothesis": "Open hardware"},
        ]
        expand_node(slug, root_id, max_children=2)

    graph = build_tree_graph(slug)
    assert graph is not None
    assert len(graph["nodes"]) == 3
    assert len(graph["edges"]) == 2
    assert all("x" in n and "y" in n for n in graph["nodes"])


def test_expand_manual_branch(trees_dir, monkeypatch) -> None:
    slug = _seed_tree(trees_dir, monkeypatch)
    from services.rnd_hypothesis_tree import expand_node, get_tree

    tree = get_tree(slug)
    root_id = tree["root_id"]
    result = expand_node(
        slug,
        root_id,
        manual={"title": "DiffusionGemma Nadia", "hypothesis": "Ack local rapide"},
    )
    assert result["children_created"] == 1
    updated = get_tree(slug)
    titles = [n["title"] for n in updated["nodes"]]
    assert "DiffusionGemma Nadia" in titles


def test_promote_node_to_dossier(trees_dir, monkeypatch) -> None:
    slug = _seed_tree(trees_dir, monkeypatch)
    from services.rnd_hypothesis_tree import (
        _load_tree,
        _save_tree,
        promote_node_to_dossier,
    )

    tree = _load_tree(slug)
    node_id = tree["root_id"]
    node = tree["nodes"][node_id]
    node["status"] = "explored"
    node["score"] = 24
    node["verdict"] = "GO"
    node["insight"] = "Insight test"
    node["evidence"] = {"key_findings": ["Point clé"]}
    _save_tree(tree)

    fake_dossier = {
        "dossier": {"id": "dossier-abc", "title": "Test", "sections_total_count": 12},
    }
    with patch("agents.rnd_center.inject_idea", return_value={"id": "idea_123", "title": "Test"}):
        with patch(
            "agents.rnd_dossier_agent.promote_idea_to_dossier",
            return_value=fake_dossier,
        ):
            result = promote_node_to_dossier(slug, node_id, enrich=False)

    assert result["success"] is True
    assert result["dossier_id"] == "dossier-abc"
    from services.rnd_hypothesis_tree import get_tree

    updated = get_tree(slug)
    root = next(n for n in updated["nodes"] if n["id"] == node_id)
    assert root["dossier_id"] == "dossier-abc"


def test_llm_benchmark_saves_result(trees_dir, monkeypatch) -> None:
    from services.rnd_llm_benchmark import get_latest_benchmark, run_llm_latency_benchmark

    with patch("agents.base.LLMClient") as llm_cls:
        llm = MagicMock()
        llm.complete.return_value = "Ack reçu — recherche R&D lancée."
        llm_cls.return_value = llm
        result = run_llm_latency_benchmark(agent_id="secretary")

    assert result["openrouter"]["avg_elapsed_ms"] is not None
    assert result["diffusion_gemma_reference"]["model"] == "DiffusionGemma"
    latest = get_latest_benchmark()
    assert latest is not None
    assert latest["id"] == result["id"]
