"""Agent action logging to Supabase."""

from __future__ import annotations

from typing import Any

from database.supabase_client import SupabaseClient


def log_agent_action(
    db: SupabaseClient,
    agent_name: str,
    action: str,
    input_summary: str,
    output_summary: str,
    status: str = "success",
    project_id: str | None = None,
) -> dict[str, Any]:
    return db.insert(
        "agent_logs",
        {
            "agent_name": agent_name,
            "action": action,
            "project_id": project_id,
            "input_summary": input_summary[:2000],
            "output_summary": output_summary[:2000],
            "status": status,
        },
    )
