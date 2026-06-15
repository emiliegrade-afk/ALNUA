"""Execute Studio Flows — topological order → sequential studio jobs."""

from __future__ import annotations

import logging
from collections import deque
from datetime import datetime, timezone
from typing import Any

from database.creatorflow_supabase_client import get_cf_supabase
from database.supabase_client import SupabaseClient
from services.studio.flows import get_studio_flow, update_studio_flow
from services.studio.jobs import create_studio_job, get_studio_job
from services.studio.runner import run_studio_job

logger = logging.getLogger(__name__)

_IMAGE_CAPS = frozenset({"image_generate", "image_enhance", "image_edit", "export_format"})
_SOURCE_TOOLS = frozenset({"upscale_image", "remove_bg", "resize_export", "runway_i2v"})


def topological_node_order(
    nodes: list[dict[str, Any]],
    edges: list[dict[str, Any]],
) -> list[str]:
    """Return node ids in dependency order (parents before children)."""
    node_ids = {str(n["id"]) for n in nodes if n.get("id")}
    if not node_ids:
        return []

    in_degree = {nid: 0 for nid in node_ids}
    adjacency: dict[str, list[str]] = {nid: [] for nid in node_ids}

    for edge in edges:
        src = str(edge.get("source") or "")
        tgt = str(edge.get("target") or "")
        if src not in node_ids or tgt not in node_ids or src == tgt:
            continue
        adjacency[src].append(tgt)
        in_degree[tgt] = in_degree.get(tgt, 0) + 1

    queue = deque(nid for nid, deg in in_degree.items() if deg == 0)
    ordered: list[str] = []

    while queue:
        current = queue.popleft()
        ordered.append(current)
        for nxt in adjacency.get(current, []):
            in_degree[nxt] -= 1
            if in_degree[nxt] == 0:
                queue.append(nxt)

    if len(ordered) != len(node_ids):
        raise ValueError("Le flow contient un cycle — corrigez les connexions")

    return ordered


def _node_by_id(nodes: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(n["id"]): n for n in nodes if n.get("id")}


def _parent_node_ids(node_id: str, edges: list[dict[str, Any]]) -> list[str]:
    return [str(e["source"]) for e in edges if str(e.get("target")) == node_id and e.get("source")]


def _inject_parent_outputs(
    tool_id: str,
    params: dict[str, Any],
    parent_jobs: list[dict[str, Any]],
) -> dict[str, Any]:
    merged = dict(params or {})
    if tool_id not in _SOURCE_TOOLS:
        return merged

    for job in reversed(parent_jobs):
        if job.get("status") != "succeeded":
            continue
        cap = job.get("capability") or ""
        tid = job.get("tool_id") or ""
        is_image = cap in _IMAGE_CAPS or "image" in tid or tid.endswith("_image")
        if not is_image:
            continue
        url = job.get("artifact_url")
        if not url:
            continue
        merged["source_image"] = url
        if job.get("asset_id"):
            merged["source_asset_id"] = job["asset_id"]
        break

    return merged


def run_studio_flow(flow_id: str, user_id: str, db: SupabaseClient | None = None) -> dict[str, Any]:
    """Run all nodes in order; each job waits for the previous wave to finish."""
    db = db or get_cf_supabase()
    flow = get_studio_flow(flow_id, user_id, db)
    if not flow:
        raise ValueError("Flow Studio introuvable")

    nodes = list(flow.get("nodes") or [])
    edges = list(flow.get("edges") or [])
    if not nodes:
        raise ValueError("Flow vide — ajoutez au moins un nœud")

    order = topological_node_order(nodes, edges)
    node_map = _node_by_id(nodes)
    idea_id = flow["idea_id"]

    started_at = datetime.now(timezone.utc).isoformat()
    node_jobs: dict[str, str] = {}
    completed_jobs: dict[str, dict[str, Any]] = {}

    update_studio_flow(
        flow_id,
        user_id,
        last_run={"status": "running", "started_at": started_at, "node_jobs": {}},
        db=db,
    )

    try:
        for node_id in order:
            node = node_map.get(node_id)
            if not node:
                continue
            data = node.get("data") or {}
            tool_id = str(data.get("tool_id") or "").strip()
            if not tool_id:
                raise ValueError(f"Nœud {node_id} sans outil")

            parent_ids = _parent_node_ids(node_id, edges)
            parent_jobs = [completed_jobs[pid] for pid in parent_ids if pid in completed_jobs]
            params = _inject_parent_outputs(tool_id, dict(data.get("params") or {}), parent_jobs)
            prompt = str(data.get("prompt") or "").strip() or None

            job = create_studio_job(
                idea_id,
                user_id,
                tool_id=tool_id,
                prompt_override=prompt,
                params=params,
                db=db,
            )
            node_jobs[node_id] = job["id"]
            run_studio_job(job["id"], user_id, db)

            finished = get_studio_job(job["id"], user_id, db)
            if not finished or finished.get("status") != "succeeded":
                err = (finished or {}).get("error_message") or "Job échoué"
                raise RuntimeError(f"{tool_id}: {err}")

            completed_jobs[node_id] = finished

        last_run = {
            "status": "succeeded",
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "node_jobs": node_jobs,
        }
        update_studio_flow(flow_id, user_id, last_run=last_run, db=db)
        logger.info("Studio flow %s succeeded (%d nodes)", flow_id, len(node_jobs))
        return last_run

    except Exception as exc:
        logger.exception("Studio flow %s failed", flow_id)
        last_run = {
            "status": "failed",
            "started_at": started_at,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "node_jobs": node_jobs,
            "error": str(exc)[:500],
        }
        update_studio_flow(flow_id, user_id, last_run=last_run, db=db)
        raise
