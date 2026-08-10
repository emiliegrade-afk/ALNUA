"""Shared storage, node helpers, and tree utilities for hypothesis trees."""

from __future__ import annotations

import json
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import logging

logger = logging.getLogger(__name__)

NodeStatus = Literal["pending", "running", "explored", "pruned", "merged", "failed"]
TreeStatus = Literal["active", "completed"]

_STATUS_ORDER = ("pending", "running", "explored", "merged", "pruned", "failed")


def _trees_dir() -> Path:
    from services.rnd_hypothesis_tree import TREES_DIR

    return TREES_DIR


def _watch_topics_file() -> Path:
    from services.rnd_hypothesis_tree import WATCH_TOPICS_FILE

    return WATCH_TOPICS_FILE


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(text: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", text.lower().strip())[:60].strip("-")
    return base or "investigation"


def _new_id() -> str:
    return str(uuid.uuid4())


def _load_watch_topics() -> list[dict[str, Any]]:
    path = _watch_topics_file()
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("topics") or []
    except Exception:
        return []


def _match_watch_topics(topic: str) -> list[dict[str, Any]]:
    lower = topic.lower()
    hits: list[dict[str, Any]] = []
    for item in _load_watch_topics():
        tags = [t.lower() for t in item.get("tags") or []]
        title = str(item.get("title", "")).lower()
        if any(t in lower for t in tags) or any(w in lower for w in title.split()[:3]):
            hits.append(item)
        elif "diffusion" in lower and "diffusion" in title:
            hits.append(item)
        elif any(k in lower for k in ("llm", "ia", "ai", "modèle", "modele", "gemma")):
            if "gemma" in title or "diffusion" in title:
                hits.append(item)
    return hits[:2]


def _tree_path(slug: str) -> Path:
    trees_dir = _trees_dir()
    trees_dir.mkdir(parents=True, exist_ok=True)
    return trees_dir / f"{slug}.json"


def _load_tree(slug: str) -> dict[str, Any] | None:
    path = _tree_path(slug)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _save_tree(tree: dict[str, Any]) -> None:
    path = _tree_path(tree["slug"])
    path.write_text(json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8")


def _node(tree: dict[str, Any], node_id: str) -> dict[str, Any]:
    nodes = tree.get("nodes") or {}
    if node_id not in nodes:
        raise KeyError(f"node {node_id} not found")
    return nodes[node_id]


def _ancestor_insights(tree: dict[str, Any], node_id: str) -> str:
    lines: list[str] = []
    nodes = tree["nodes"]
    current = nodes.get(node_id)
    visited = 0
    while current and current.get("parent_id") and visited < 8:
        parent = nodes.get(current["parent_id"])
        if not parent:
            break
        if parent.get("insight"):
            lines.append(f"- [{parent.get('status')}] {parent['title']}: {parent['insight']}")
        current = parent
        visited += 1
    return "\n".join(lines)


def _serialize_tree(tree: dict[str, Any]) -> dict[str, Any]:
    nodes = list((tree.get("nodes") or {}).values())
    nodes.sort(key=lambda n: n.get("created_at", ""))
    return {
        **tree,
        "nodes": nodes,
        "stats": _tree_stats(tree),
    }


def _tree_stats(tree: dict[str, Any]) -> dict[str, int]:
    nodes = tree.get("nodes") or {}
    stats = {s: 0 for s in _STATUS_ORDER}
    for node in nodes.values():
        st = node.get("status", "pending")
        if st in stats:
            stats[st] += 1
    return stats


def _make_node(
    *,
    title: str,
    hypothesis: str,
    parent_id: str | None,
    depth: int = 0,
) -> dict[str, Any]:
    now = _utc_now()
    return {
        "id": _new_id(),
        "parent_id": parent_id,
        "title": title[:200],
        "hypothesis": hypothesis[:2000],
        "status": "pending",
        "depth": depth,
        "score": None,
        "verdict": None,
        "insight": "",
        "evidence": {},
        "report_markdown": None,
        "children": [],
        "idea_id": None,
        "dossier_id": None,
        "created_at": now,
        "updated_at": now,
    }


def _patch_idea_fields(idea_id: str | None, fields: dict[str, Any]) -> None:
    if not idea_id:
        return
    try:
        from agents.rnd_center import RND_IDEAS_FILE

        ideas = json.loads(RND_IDEAS_FILE.read_text(encoding="utf-8"))
        for idea in ideas:
            if idea.get("id") == idea_id:
                idea.update(fields)
                break
        RND_IDEAS_FILE.write_text(
            json.dumps(ideas, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        logger.debug("patch idea fields failed", exc_info=True)


def _recompute_depths(tree: dict[str, Any], node_id: str, base_depth: int) -> None:
    """Recalcule depth pour un nœud + tout son sous-arbre après un reparent."""
    node = tree["nodes"].get(node_id)
    if not node:
        return
    node["depth"] = base_depth
    for child_id in node.get("children") or []:
        _recompute_depths(tree, child_id, base_depth + 1)
