"""Node execution, expansion, and async tree worker for hypothesis trees."""

from __future__ import annotations

import logging
from typing import Any

from services.rnd_hypothesis_tree_helpers import (
    _load_tree,
    _make_node,
    _node,
    _patch_idea_fields,
    _save_tree,
    _tree_stats,
    _utc_now,
)
from services.rnd_hypothesis_tree_llm import (
    _evaluate_node,
    _format_node_report,
    _run_investigation,
)

logger = logging.getLogger(__name__)


def _backpropagate(tree: dict[str, Any], node_id: str) -> None:
    node = _node(tree, node_id)
    parent_id = node.get("parent_id")
    if not parent_id or not node.get("insight"):
        return
    parent = _node(tree, parent_id)
    child_insight = node.get("insight", "")
    if child_insight and child_insight not in (parent.get("insight") or ""):
        combined = (parent.get("insight") or "").strip()
        if combined:
            combined += "\n"
        parent["insight"] = (combined + f"[{node['status']}] {child_insight}")[:1500]
        parent["updated_at"] = _utc_now()


def _execute_node(
    tree_slug: str,
    node_id: str,
    *,
    chat_id: int | None = None,
    notify: bool = True,
) -> None:
    tree = _load_tree(tree_slug)
    if not tree:
        return
    node = _node(tree, node_id)
    if node.get("status") not in ("pending", "running"):
        return

    node["status"] = "running"
    node["updated_at"] = _utc_now()
    _save_tree(tree)

    topic = tree["topic"]
    query = f"{topic} — {node['hypothesis']}"[:400]

    try:
        from agents.rnd_center import get_vision

        vision = get_vision()
        report = _run_investigation(query)
        evaluation = _evaluate_node(node["hypothesis"], report, vision)

        node["evidence"] = {
            "key_findings": (report.get("key_findings") or [])[:5],
            "recommended_actions": (report.get("recommended_actions") or [])[:3],
        }
        node["report_markdown"] = _format_node_report(topic, node, report)
        node["score"] = evaluation.get("score")
        node["verdict"] = evaluation.get("verdict")
        node["insight"] = evaluation.get("insight", "")
        node["status"] = evaluation.get("status", "explored")
        node["updated_at"] = _utc_now()

        _backpropagate(tree, node_id)

        if node["status"] == "merged":
            try:
                from agents.rnd_center import inject_idea

                idea = inject_idea(
                    f"{node['title']}: {node['hypothesis'][:300]}",
                    source=f"hypothesis_tree:{tree_slug}",
                )
                node["idea_id"] = idea.get("id")
                if node.get("score") is not None:
                    ideas_path_updates = {
                        "score": node["score"],
                        "verdict": node.get("verdict"),
                        "status": "evaluated_merged",
                    }
                    _patch_idea_fields(idea.get("id"), ideas_path_updates)
            except Exception:
                logger.debug("inject merged node as idea skipped", exc_info=True)

        _save_tree(tree)

        if notify and chat_id and node.get("report_markdown"):
            from skills.skill_telegram_notify import notify_telegram

            status_emoji = {"merged": "★", "pruned": "✂️", "explored": "🔍"}.get(
                node["status"], "•"
            )
            msg = (
                f"{status_emoji} **Branche {node['status'].upper()}** — {node['title']}\n"
                f"Score : {node.get('score', '?')}/30 · {node.get('verdict', '?')}\n"
                f"Insight : {node.get('insight', '')[:200]}\n\n"
                f"{node['report_markdown'][:2800]}"
            )
            notify_telegram(msg, chat_id=chat_id)

    except Exception as exc:
        logger.exception("hypothesis node execution failed: %s", node_id)
        node["status"] = "failed"
        node["insight"] = str(exc)[:300]
        node["updated_at"] = _utc_now()
        _save_tree(tree)
        if notify and chat_id:
            from skills.skill_telegram_notify import notify_telegram

            notify_telegram(
                f"❌ Branche échouée — {node['title']}: {exc}",
                chat_id=chat_id,
            )


def _expand_tree(tree_slug: str, parent_id: str, *, max_children: int = 3) -> list[str]:
    import services.rnd_hypothesis_tree as facade

    tree = _load_tree(tree_slug)
    if not tree:
        return []
    parent = _node(tree, parent_id)
    branches = facade._ideate_branches(tree["topic"], parent, tree, max_count=max_children)
    child_ids: list[str] = []
    for branch in branches:
        child = _make_node(
            title=branch["title"],
            hypothesis=branch["hypothesis"],
            parent_id=parent_id,
            depth=int(parent.get("depth", 0)) + 1,
        )
        tree["nodes"][child["id"]] = child
        parent.setdefault("children", []).append(child["id"])
        child_ids.append(child["id"])
    parent["updated_at"] = _utc_now()
    tree["updated_at"] = _utc_now()
    _save_tree(tree)
    return child_ids


def _run_tree_worker(tree_slug: str, chat_id: int | None) -> None:
    tree = _load_tree(tree_slug)
    if not tree:
        return

    root_id = tree["root_id"]
    _execute_node(tree_slug, root_id, chat_id=chat_id, notify=False)

    child_ids = _expand_tree(tree_slug, root_id, max_children=3)
    for cid in child_ids:
        _execute_node(tree_slug, cid, chat_id=chat_id, notify=True)

    tree = _load_tree(tree_slug)
    if not tree:
        return
    tree["status"] = "completed"
    tree["updated_at"] = _utc_now()
    _save_tree(tree)

    if chat_id:
        from skills.skill_telegram_notify import notify_telegram

        stats = _tree_stats(tree)
        merged = [n for n in tree["nodes"].values() if n.get("status") == "merged"]
        lines = [
            f"🌳 **Arbre R&D terminé** — « {tree['topic'][:80]} »",
            f"Branches : {stats.get('explored', 0)} explorées · "
            f"{stats.get('merged', 0)} mergées · {stats.get('pruned', 0)} élaguées",
        ]
        if merged:
            lines.append("\n**Candidats promote dossier :**")
            for m in merged[:3]:
                lines.append(f"★ {m['title']} ({m.get('score', '?')}/30)")
        lines.append("\nVoir l'arbre dans le Hub → Centre R&D → Arbres.")
        notify_telegram("\n".join(lines), chat_id=chat_id)
