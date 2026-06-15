"""Studio Flows — persisted node graphs per idea."""

from __future__ import annotations

from typing import Any

from database.creatorflow_supabase_client import get_cf_supabase
from database.supabase_client import SupabaseClient
from services.creatorflow_ideas import get_cf_idea

_CF_FLOWS = "cf_studio_flows"

DEFAULT_FLOW_NAME = "Studio Flow"


def default_flow_graph() -> dict[str, list[dict[str, Any]]]:
    """Starter: Image → TTS → Resize (spec Bloc H)."""
    return {
        "nodes": [
            {
                "id": "n1",
                "type": "studioTool",
                "position": {"x": 120, "y": 80},
                "data": {
                    "tool_id": "imagen_image",
                    "label": "Image feed",
                    "prompt": "",
                    "params": {},
                },
            },
            {
                "id": "n2",
                "type": "studioTool",
                "position": {"x": 120, "y": 240},
                "data": {
                    "tool_id": "google_tts",
                    "label": "Voix off",
                    "prompt": "",
                    "params": {},
                },
            },
            {
                "id": "n3",
                "type": "studioTool",
                "position": {"x": 120, "y": 400},
                "data": {
                    "tool_id": "resize_export",
                    "label": "Export 9:16",
                    "prompt": "",
                    "params": {"aspect_ratio": "9:16"},
                },
            },
        ],
        "edges": [
            {"id": "e1-2", "source": "n1", "target": "n2"},
            {"id": "e2-3", "source": "n2", "target": "n3"},
            {"id": "e1-3", "source": "n1", "target": "n3"},
        ],
    }


def list_studio_flows_for_idea(
    idea_id: str,
    user_id: str,
    db: SupabaseClient | None = None,
) -> list[dict[str, Any]]:
    db = db or get_cf_supabase()
    if not get_cf_idea(idea_id, user_id, db):
        return []
    return db.select(
        _CF_FLOWS,
        filters={"idea_id": idea_id, "user_id": user_id},
        order_by="updated_at",
        ascending=False,
    )


def get_studio_flow(
    flow_id: str,
    user_id: str,
    db: SupabaseClient | None = None,
) -> dict[str, Any] | None:
    db = db or get_cf_supabase()
    rows = db.select(_CF_FLOWS, filters={"id": flow_id, "user_id": user_id}, limit=1)
    return rows[0] if rows else None


def create_studio_flow(
    idea_id: str,
    user_id: str,
    *,
    name: str | None = None,
    nodes: list[dict[str, Any]] | None = None,
    edges: list[dict[str, Any]] | None = None,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    db = db or get_cf_supabase()
    idea = get_cf_idea(idea_id, user_id, db)
    if not idea:
        raise ValueError("Idée introuvable")

    graph = default_flow_graph()
    payload_nodes = nodes if nodes is not None else graph["nodes"]
    payload_edges = edges if edges is not None else graph["edges"]

    return db.insert(
        _CF_FLOWS,
        {
            "user_id": user_id,
            "project_id": idea.get("project_id"),
            "idea_id": idea_id,
            "name": (name or DEFAULT_FLOW_NAME).strip()[:200],
            "nodes": payload_nodes,
            "edges": payload_edges,
            "last_run": None,
        },
    )


def update_studio_flow(
    flow_id: str,
    user_id: str,
    *,
    name: str | None = None,
    nodes: list[dict[str, Any]] | None = None,
    edges: list[dict[str, Any]] | None = None,
    last_run: dict[str, Any] | None = None,
    db: SupabaseClient | None = None,
) -> dict[str, Any]:
    db = db or get_cf_supabase()
    flow = get_studio_flow(flow_id, user_id, db)
    if not flow:
        raise ValueError("Flow Studio introuvable")

    patch: dict[str, Any] = {}
    if name is not None:
        patch["name"] = name.strip()[:200]
    if nodes is not None:
        patch["nodes"] = nodes
    if edges is not None:
        patch["edges"] = edges
    if last_run is not None:
        patch["last_run"] = last_run

    if not patch:
        return flow

    return db.update(_CF_FLOWS, flow_id, patch)


def delete_studio_flow(
    flow_id: str,
    user_id: str,
    db: SupabaseClient | None = None,
) -> None:
    db = db or get_cf_supabase()
    flow = get_studio_flow(flow_id, user_id, db)
    if not flow:
        raise ValueError("Flow Studio introuvable")
    db.delete(_CF_FLOWS, flow_id)
