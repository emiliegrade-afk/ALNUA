"""Public mutation APIs for hypothesis trees."""

from __future__ import annotations

import logging
from typing import Any

from services.rnd_hypothesis_tree_execution import (
    _execute_node,
    _expand_tree,
    _run_tree_worker,
)
from services.rnd_hypothesis_tree_helpers import (
    _load_tree,
    _make_node,
    _match_watch_topics,
    _new_id,
    _node,
    _recompute_depths,
    _save_tree,
    _slugify,
    _tree_path,
    _tree_stats,
    _utc_now,
)
from services.rnd_hypothesis_tree_promote import promote_node_to_dossier

logger = logging.getLogger(__name__)


def start_investigation(
    topic: str,
    *,
    requested_by: str = "ceo",
    chat_id: int | None = None,
    expand: bool = True,
) -> dict[str, Any]:
    """
    Create hypothesis tree and run async investigation (Arbor-lite phase 1).
    Returns immediately with tree metadata.
    """
    import services.rnd_hypothesis_tree as facade

    topic = topic.strip()
    if len(topic) < 3:
        raise ValueError("Sujet trop court")

    slug_base = _slugify(topic)
    slug = slug_base
    counter = 1
    while _tree_path(slug).exists():
        slug = f"{slug_base}-{counter}"
        counter += 1

    now = _utc_now()
    root = _make_node(
        title=f"Marché & opportunités — {topic[:80]}",
        hypothesis=f"Cartographier les opportunités ALNUA autour de : {topic}",
        parent_id=None,
        depth=0,
    )

    tree: dict[str, Any] = {
        "id": _new_id(),
        "slug": slug,
        "topic": topic,
        "status": "active",
        "root_id": root["id"],
        "requested_by": requested_by,
        "watch_topics": [w.get("id") for w in _match_watch_topics(topic)],
        "nodes": {root["id"]: root},
        "created_at": now,
        "updated_at": now,
    }
    _save_tree(tree)

    facade.threading.Thread(
        target=_run_tree_worker,
        args=(slug, chat_id),
        daemon=False,
        name=f"rnd-tree-{slug[:24]}",
    ).start()

    watch_names = [w.get("title", "") for w in _match_watch_topics(topic)]
    message = (
        f"Arbre d'hypothèses lancé sur « {topic} » — "
        "racine + 3 branches en investigation (~3-8 min)."
    )
    if watch_names:
        message += f" Veille activée : {', '.join(watch_names[:2])}."

    return {
        "success": True,
        "slug": slug,
        "topic": topic,
        "status": "active",
        "root_id": root["id"],
        "message": message,
        "hub_path": f"/rnd?tree={slug}",
    }


def expand_node(
    slug: str,
    node_id: str,
    *,
    max_children: int = 3,
    run_after: bool = False,
    manual: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Ideate (or manual) child branches under a node."""
    import services.rnd_hypothesis_tree as facade

    tree = _load_tree(slug)
    if not tree:
        raise ValueError("Arbre introuvable")
    parent = _node(tree, node_id)

    child_ids: list[str] = []
    if manual and manual.get("title"):
        child = _make_node(
            title=manual["title"],
            hypothesis=manual.get("hypothesis") or manual["title"],
            parent_id=node_id,
            depth=int(parent.get("depth", 0)) + 1,
        )
        tree["nodes"][child["id"]] = child
        parent.setdefault("children", []).append(child["id"])
        child_ids.append(child["id"])
        tree["updated_at"] = _utc_now()
        _save_tree(tree)
    else:
        child_ids = _expand_tree(slug, node_id, max_children=max_children)

    if run_after and child_ids:
        for cid in child_ids:
            facade.threading.Thread(
                target=_execute_node,
                args=(slug, cid),
                kwargs={"notify": False},
                daemon=True,
                name=f"rnd-node-{cid[:8]}",
            ).start()

    tree = _load_tree(slug)
    return {
        "success": True,
        "child_ids": child_ids,
        "children_created": len(child_ids),
        "stats": _tree_stats(tree) if tree else {},
    }


def run_node(slug: str, node_id: str, *, chat_id: int | None = None) -> dict[str, Any]:
    """Run investigation on a single pending/explored node (async)."""
    import services.rnd_hypothesis_tree as facade

    tree = _load_tree(slug)
    if not tree:
        raise ValueError("Arbre introuvable")
    node = _node(tree, node_id)
    if node.get("status") == "running":
        return {"success": True, "status": "running", "message": "Déjà en cours"}

    facade.threading.Thread(
        target=_execute_node,
        args=(slug, node_id),
        kwargs={"chat_id": chat_id, "notify": False},
        daemon=True,
        name=f"rnd-run-{node_id[:8]}",
    ).start()
    return {"success": True, "status": "started", "node_id": node_id}


def set_node_status(slug: str, node_id: str, status: str) -> dict[str, Any]:
    """Manual CEO override: prune, merge, or reset to explored."""
    allowed = {"pending", "explored", "pruned", "merged"}
    if status not in allowed:
        raise ValueError(f"Statut invalide : {status}")
    tree = _load_tree(slug)
    if not tree:
        raise ValueError("Arbre introuvable")
    node = _node(tree, node_id)
    node["status"] = status
    node["updated_at"] = _utc_now()
    if status == "merged" and not node.get("idea_id"):
        try:
            from agents.rnd_center import inject_idea

            idea = inject_idea(
                f"{node['title']}: {node.get('hypothesis', '')[:400]}",
                source=f"hypothesis_tree:{slug}",
            )
            node["idea_id"] = idea.get("id")
        except Exception:
            pass
    tree["updated_at"] = _utc_now()
    _save_tree(tree)
    return {"success": True, "node_id": node_id, "status": status}


def reparent_node(slug: str, node_id: str, new_parent_id: str) -> dict[str, Any]:
    """Glisser un nœud sur un autre = "relier" (Phase 26, ROADMAP.md)."""
    tree = _load_tree(slug)
    if not tree:
        raise ValueError("Arbre introuvable")
    node = _node(tree, node_id)
    new_parent = _node(tree, new_parent_id)

    if node_id == new_parent_id:
        raise ValueError("Un nœud ne peut pas être son propre parent")
    if node_id == tree.get("root_id"):
        raise ValueError("La racine de l'arbre ne peut pas être déplacée")

    descendants: set[str] = set()
    queue = list(node.get("children") or [])
    while queue:
        cid = queue.pop()
        if cid in descendants:
            continue
        descendants.add(cid)
        child = tree["nodes"].get(cid)
        if child:
            queue.extend(child.get("children") or [])
    if new_parent_id in descendants:
        raise ValueError("Impossible de relier un nœud à l'un de ses propres descendants")

    old_parent_id = node.get("parent_id")
    if old_parent_id and old_parent_id in tree["nodes"]:
        old_parent = tree["nodes"][old_parent_id]
        old_parent["children"] = [c for c in old_parent.get("children", []) if c != node_id]
        old_parent["updated_at"] = _utc_now()

    node["parent_id"] = new_parent_id
    new_parent.setdefault("children", []).append(node_id)
    new_parent["updated_at"] = _utc_now()
    _recompute_depths(tree, node_id, int(new_parent.get("depth", 0)) + 1)
    node["updated_at"] = _utc_now()
    tree["updated_at"] = _utc_now()
    _save_tree(tree)
    return {"success": True, "node_id": node_id, "new_parent_id": new_parent_id}


__all__ = [
    "expand_node",
    "promote_node_to_dossier",
    "reparent_node",
    "run_node",
    "set_node_status",
    "start_investigation",
]
