"""
Arbor-inspired hypothesis tree for ALNUA R&D.

Coordinator (this module) owns persistent trees; executors run isolated
investigations and return evidence. Insights backpropagate to ancestors.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from config.paths import data_dir

logger = logging.getLogger(__name__)

NodeStatus = Literal["pending", "running", "explored", "pruned", "merged", "failed"]
TreeStatus = Literal["active", "completed"]

TREES_DIR = data_dir("rnd_trees")
WATCH_TOPICS_FILE = data_dir("rnd_watch_topics.json")

_STATUS_ORDER = ("pending", "running", "explored", "merged", "pruned", "failed")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slugify(text: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", text.lower().strip())[:60].strip("-")
    return base or "investigation"


def _new_id() -> str:
    return str(uuid.uuid4())


def _load_watch_topics() -> list[dict[str, Any]]:
    if not WATCH_TOPICS_FILE.exists():
        return []
    try:
        data = json.loads(WATCH_TOPICS_FILE.read_text(encoding="utf-8"))
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
    TREES_DIR.mkdir(parents=True, exist_ok=True)
    return TREES_DIR / f"{slug}.json"


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


def list_trees(*, limit: int = 20) -> list[dict[str, Any]]:
    TREES_DIR.mkdir(parents=True, exist_ok=True)
    trees: list[dict[str, Any]] = []
    for path in sorted(TREES_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
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


def _ideate_branches(topic: str, parent: dict[str, Any], tree: dict[str, Any], *, max_count: int = 3) -> list[dict[str, str]]:
    """Propose child hypotheses conditioned on topic + ancestor insights."""
    from agents.base import LLMClient, parse_json_response

    ancestors = _ancestor_insights(tree, parent["id"])
    watch = _match_watch_topics(topic)
    watch_block = ""
    if watch:
        parts = []
        for w in watch:
            parts.append(f"**{w.get('title')}** — {w.get('summary', '')[:300]}")
            for branch in w.get("suggested_branches") or []:
                parts.append(f"  → branche suggérée : {branch}")
        watch_block = "\n\nVeille R&D ALNUA (prioriser si pertinent) :\n" + "\n".join(parts)

    system = """Tu es Alex Mercer, lead R&D ALNUA (solopreneuse CEO Emilie).
Propose des hypothèses ENFANTS testables pour un arbre de recherche (style Arbor).
Chaque branche = une direction produit/marché distincte, pas un doublon.

JSON uniquement :
{
  "branches": [
    {"title": "Nom court", "hypothesis": "Ce qu'on teste et pourquoi ALNUA"}
  ]
}

Règles :
- 2 à 3 branches max
- Diversité : gaming, robotique, SaaS, hardware, IA tooling — pas que vanlife
- Si une veille est fournie (ex. DiffusionGemma), au moins une branche peut l'exploiter
- Évite les hypothèses déjà explorées/prunées listées"""

    pruned = [
        f"- {n['title']}: {n.get('insight', '')[:120]}"
        for n in (tree.get("nodes") or {}).values()
        if n.get("status") == "pruned"
    ]
    pruned_block = "\n".join(pruned[:6]) if pruned else "aucune"

    user = f"""Sujet racine : {topic}
Parent : {parent['title']}
Hypothèse parent : {parent.get('hypothesis', '')[:400]}

Insights ancêtres :
{ancestors or 'aucun'}

Branches déjà écartées :
{pruned_block}
{watch_block}

Propose {max_count} branches enfants."""

    try:
        llm = LLMClient()
        raw = llm.complete(system, user, agent_id="rnd_agent", temperature=0.7)
        parsed = parse_json_response(raw)
        branches = parsed.get("branches") or []
        out: list[dict[str, str]] = []
        for b in branches[:max_count]:
            if isinstance(b, dict) and b.get("title"):
                out.append(
                    {
                        "title": str(b["title"])[:200],
                        "hypothesis": str(b.get("hypothesis") or b["title"])[:2000],
                    }
                )
        if out:
            return out
    except Exception as exc:
        logger.warning("hypothesis ideation LLM failed: %s", exc)

    # Fallback branches
    return [
        {
            "title": f"{topic} — marché B2B",
            "hypothesis": f"Opportunité B2B autour de {topic} pour PME tech",
        },
        {
            "title": f"{topic} — intégration Hub ALNUA",
            "hypothesis": f"Comment {topic} améliore les agents ou réduit les coûts Hub",
        },
        {
            "title": f"{topic} — produit consommateur",
            "hypothesis": f"Version grand public / indie viable pour {topic}",
        },
    ][:max_count]


def _evaluate_node(hypothesis: str, report: dict[str, Any], vision: str) -> dict[str, Any]:
    from agents.base import LLMClient, parse_json_response

    summary = report.get("executive_summary") or ""
    findings = report.get("key_findings") or []
    findings_text = "\n".join(f"- {f}" for f in findings[:6])

    system = """Tu évalues une hypothèse R&D après investigation.
JSON uniquement :
{
  "market_score": 7,
  "feasibility_score": 6,
  "vision_score": 7,
  "total": 20,
  "verdict": "GO|MAYBE|NO",
  "insight": "Leçon courte à transmettre aux branches sœurs (1-2 phrases)",
  "decision": "merged|explored|pruned"
}

decision :
- merged si total >= 22 et opportunité claire pour ALNUA
- pruned si total < 14 ou marché/hypothèse invalidée
- explored sinon"""

    user = f"""VISION : {vision[:400]}
HYPOTHÈSE : {hypothesis[:500]}
RÉSUMÉ : {summary[:800]}
FINDINGS :
{findings_text[:1200]}"""

    try:
        llm = LLMClient()
        raw = llm.complete(system, user, agent_id="rnd_agent", temperature=0.3)
        parsed = parse_json_response(raw)
        decision = str(parsed.get("decision", "explored")).lower()
        if decision not in ("merged", "explored", "pruned"):
            total = int(parsed.get("total") or 0)
            decision = "merged" if total >= 22 else "pruned" if total < 14 else "explored"
        status: NodeStatus = decision  # type: ignore[assignment]
        return {
            "score": parsed.get("total"),
            "verdict": parsed.get("verdict"),
            "insight": str(parsed.get("insight") or "")[:500],
            "status": status,
            "scores_detail": {
                "market": parsed.get("market_score"),
                "feasibility": parsed.get("feasibility_score"),
                "vision": parsed.get("vision_score"),
            },
        }
    except Exception as exc:
        logger.warning("node evaluation failed: %s", exc)
        return {
            "score": None,
            "verdict": "MAYBE",
            "insight": summary[:300] if summary else "Investigation terminée — évaluation manuelle recommandée.",
            "status": "explored",
            "scores_detail": {},
        }


def _run_investigation(query: str) -> dict[str, Any]:
    from services.deep_research import quick_research
    from skills.skill_web_research import _search

    web_hits = _search(query, max_results=5)
    context_parts = [
        f"- {hit.get('title', '')}: {(hit.get('content') or '')[:250]}"
        for hit in web_hits
        if hit.get("title") or hit.get("content")
    ]
    context = "Résultats web récents:\n" + "\n".join(context_parts) if context_parts else ""
    return quick_research(query=query, context=context, agent_id="rnd_agent")


def _format_node_report(topic: str, node: dict[str, Any], report: dict[str, Any]) -> str:
    from services.coo_telegram_intents import _format_investigation_report

    header = f"🌳 **Arbre R&D** — branche « {node['title']} »\nSujet : {topic[:80]}\n\n"
    return header + _format_investigation_report(node["hypothesis"], report)[:3500]


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
    tree = _load_tree(tree_slug)
    if not tree:
        return []
    parent = _node(tree, parent_id)
    branches = _ideate_branches(tree["topic"], parent, tree, max_count=max_children)
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

    threading.Thread(
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


def get_watch_topics() -> list[dict[str, Any]]:
    return _load_watch_topics()


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


def build_tree_graph(slug: str) -> dict[str, Any] | None:
    """Nodes + edges + layout positions for interactive graph UI."""
    tree = _load_tree(slug)
    if not tree:
        return None

    nodes_map = tree.get("nodes") or {}
    root_id = tree.get("root_id")
    if not root_id or root_id not in nodes_map:
        return None

    # Level-order for layout
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
    positions: dict[str, tuple[float, float]] = {}

    for depth, row in enumerate(levels):
        row_w = len(row) * node_w + max(0, len(row) - 1) * gap_x
        start_x = -row_w / 2 + node_w / 2
        for i, nid in enumerate(row):
            x = start_x + i * (node_w + gap_x)
            y = depth * (node_h + gap_y)
            positions[nid] = (x, y)
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


def expand_node(
    slug: str,
    node_id: str,
    *,
    max_children: int = 3,
    run_after: bool = False,
    manual: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Ideate (or manual) child branches under a node."""
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
            threading.Thread(
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
    tree = _load_tree(slug)
    if not tree:
        raise ValueError("Arbre introuvable")
    node = _node(tree, node_id)
    if node.get("status") == "running":
        return {"success": True, "status": "running", "message": "Déjà en cours"}

    threading.Thread(
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


def promote_node_to_dossier(slug: str, node_id: str, *, enrich: bool = True) -> dict[str, Any]:
    """Create idea (if needed) + promote to R&D dossier in one step."""
    tree = _load_tree(slug)
    if not tree:
        raise ValueError("Arbre introuvable")
    node = _node(tree, node_id)

    if node.get("dossier_id"):
        return {
            "success": True,
            "already": True,
            "dossier_id": node["dossier_id"],
            "idea_id": node.get("idea_id"),
            "message": "Dossier déjà créé pour cette branche.",
        }

    from agents.rnd_center import inject_idea
    from agents.rnd_dossier_agent import promote_idea_to_dossier

    idea_id = node.get("idea_id")
    if not idea_id:
        findings = node.get("evidence", {}).get("key_findings") or []
        findings_text = "\n".join(f"- {f}" for f in findings[:5])
        body = (
            f"{node.get('title', 'Concept R&D')}\n\n"
            f"{node.get('hypothesis', '')}\n\n"
            f"Insight arbre : {node.get('insight', '')}\n\n"
            f"Findings :\n{findings_text}"
        ).strip()
        idea = inject_idea(body[:2000], source=f"hypothesis_tree:{slug}")
        idea_id = idea.get("id")
        node["idea_id"] = idea_id
        if node.get("score") is not None:
            _patch_idea_fields(
                idea_id,
                {
                    "score": node["score"],
                    "verdict": node.get("verdict") or "MAYBE",
                    "status": "evaluated_go" if node.get("verdict") == "GO" else "evaluated_maybe",
                    "title": node.get("title", idea.get("title")),
                    "description": body[:2000],
                },
            )

    if not idea_id:
        raise RuntimeError("Impossible de créer l'idée R&D")

    result = promote_idea_to_dossier(str(idea_id), actor="emilie", enrich=False)
    dossier_id = result["dossier"]["id"]
    node["dossier_id"] = dossier_id
    if node.get("status") not in ("merged", "pruned"):
        node["status"] = "merged"
    node["updated_at"] = _utc_now()
    tree["updated_at"] = _utc_now()
    _save_tree(tree)

    if enrich:
        import threading
        from agents.rnd_dossier_agent import RndDossierAgent

        def _enrich_bg() -> None:
            try:
                RndDossierAgent().enrich_dossier(dossier_id, actor="rnd_dossier_agent")
            except Exception:
                logger.exception("enrich after tree promote failed")

        threading.Thread(target=_enrich_bg, daemon=True).start()
        result["enriching"] = True
        result["message"] = (
            f"Dossier « {result['dossier']['title']} » créé — enrichissement en cours (30–60 s)."
        )
    else:
        result["enriching"] = False

    result["success"] = True
    result["idea_id"] = idea_id
    result["dossier_id"] = dossier_id
    result["tree_slug"] = slug
    result["node_id"] = node_id
    return result

