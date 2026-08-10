"""Read-only queries and graph layout for hypothesis trees."""

from __future__ import annotations

import json
from typing import Any

from services.rnd_hypothesis_tree_helpers import (
    _load_tree,
    _load_watch_topics,
    _serialize_tree,
    _trees_dir,
)


def list_trees(*, limit: int = 20) -> list[dict[str, Any]]:
    trees_dir = _trees_dir()
    trees_dir.mkdir(parents=True, exist_ok=True)
    trees: list[dict[str, Any]] = []
    for path in sorted(trees_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            tree = json.loads(path.read_text(encoding="utf-8"))
            nodes = tree.get("nodes") or {}
            trees.append(
                {
                    "slug": tree.get("slug"),
                    "topic": tree.get("topic"),
                    "status": tree.get("status", "active"),
                    "created_at": tree.get("created_at"),
                    "updated_at": tree.get("updated_at"),
                    "node_count": len(nodes),
                    "merged_count": sum(1 for n in nodes.values() if n.get("status") == "merged"),
                    "pruned_count": sum(1 for n in nodes.values() if n.get("status") == "pruned"),
                }
            )
        except Exception:
            continue
        if len(trees) >= limit:
            break
    return trees


def get_tree(slug: str) -> dict[str, Any] | None:
    tree = _load_tree(slug)
    if not tree:
        return None
    return _serialize_tree(tree)


def get_watch_topics() -> list[dict[str, Any]]:
    return _load_watch_topics()


def build_tree_graph(slug: str) -> dict[str, Any] | None:
    """Nodes + edges + layout positions for interactive graph UI."""
    tree = _load_tree(slug)
    if not tree:
        return None

    nodes_map = tree.get("nodes") or {}
    root_id = tree.get("root_id")
    if not root_id or root_id not in nodes_map:
        return None

    levels: list[list[str]] = []
    queue: list[tuple[str, int]] = [(root_id, 0)]
    seen: set[str] = set()
    while queue:
        nid, depth = queue.pop(0)
        if nid in seen:
            continue
        seen.add(nid)
        while len(levels) <= depth:
            levels.append([])
        levels[depth].append(nid)
        node = nodes_map[nid]
        for cid in node.get("children") or []:
            if cid in nodes_map:
                queue.append((cid, depth + 1))

    node_w, node_h, gap_x, gap_y = 200, 72, 48, 90
    graph_nodes: list[dict[str, Any]] = []

    for depth, row in enumerate(levels):
        row_w = len(row) * node_w + max(0, len(row) - 1) * gap_x
        start_x = -row_w / 2 + node_w / 2
        for i, nid in enumerate(row):
            x = start_x + i * (node_w + gap_x)
            y = depth * (node_h + gap_y)
            n = nodes_map[nid]
            graph_nodes.append(
                {
                    "id": nid,
                    "parent_id": n.get("parent_id"),
                    "title": n.get("title"),
                    "status": n.get("status"),
                    "score": n.get("score"),
                    "verdict": n.get("verdict"),
                    "depth": n.get("depth", depth),
                    "idea_id": n.get("idea_id"),
                    "dossier_id": n.get("dossier_id"),
                    "x": x,
                    "y": y,
                }
            )

    edges: list[dict[str, str]] = []
    for nid, n in nodes_map.items():
        for cid in n.get("children") or []:
            if cid in nodes_map:
                edges.append({"from": nid, "to": cid})

    width = max((len(row) for row in levels), default=1) * (node_w + gap_x)
    height = len(levels) * (node_h + gap_y)

    return {
        "slug": slug,
        "topic": tree.get("topic"),
        "root_id": root_id,
        "nodes": graph_nodes,
        "edges": edges,
        "width": width,
        "height": height,
    }
