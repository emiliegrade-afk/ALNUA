"""Tests for Studio Flows — topo sort, CRUD, run orchestration."""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import patch

import pytest

from services.studio.flow_runner import topological_node_order, run_studio_flow
from services.studio.flows import create_studio_flow, get_studio_flow


def test_topological_order_linear() -> None:
    nodes = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
    edges = [
        {"id": "e1", "source": "a", "target": "b"},
        {"id": "e2", "source": "b", "target": "c"},
    ]
    assert topological_node_order(nodes, edges) == ["a", "b", "c"]


def test_topological_order_detects_cycle() -> None:
    nodes = [{"id": "a"}, {"id": "b"}]
    edges = [
        {"id": "e1", "source": "a", "target": "b"},
        {"id": "e2", "source": "b", "target": "a"},
    ]
    with pytest.raises(ValueError, match="cycle"):
        topological_node_order(nodes, edges)


class _FlowDB:
    def __init__(self) -> None:
        self._flows: dict[str, dict[str, Any]] = {}
        self._ideas = {
            "idea-1": {
                "id": "idea-1",
                "user_id": "user-1",
                "project_id": "proj-1",
                "content": "Test idea",
                "status": "ready_to_shoot",
            }
        }
        self._jobs: dict[str, dict[str, Any]] = {}

    def select(self, table: str, filters: dict[str, Any] | None = None, **kwargs: Any) -> list[dict[str, Any]]:
        store = self._flows if table == "cf_studio_flows" else self._ideas
        filters = filters or {}
        rows = list(store.values())
        for key, value in filters.items():
            rows = [r for r in rows if r.get(key) == value]
        limit = kwargs.get("limit")
        if limit:
            rows = rows[:limit]
        return rows

    def insert(self, table: str, row: dict[str, Any]) -> dict[str, Any]:
        if table == "cf_studio_flows":
            fid = row.get("id") or str(uuid.uuid4())
            stored = {"id": fid, **row}
            self._flows[fid] = stored
            return stored
        raise KeyError(table)

    def update(self, table: str, row_id: str, values: dict[str, Any], id_column: str = "id") -> dict[str, Any]:
        if table == "cf_studio_flows":
            self._flows[row_id] = {**self._flows[row_id], **values}
            return self._flows[row_id]
        raise KeyError(table)


@patch("services.studio.flow_runner.get_studio_job")
@patch("services.studio.flow_runner.run_studio_job")
@patch("services.studio.flow_runner.create_studio_job")
def test_run_studio_flow_executes_in_order(
    mock_create: Any,
    mock_run: Any,
    mock_get_job: Any,
) -> None:
    db = _FlowDB()
    flow = create_studio_flow("idea-1", "user-1", db=db)  # type: ignore[arg-type]

    job_ids = ["j1", "j2", "j3"]
    mock_create.side_effect = [
        {"id": jid, "tool_id": tid, "status": "queued", "idea_id": "idea-1"}
        for jid, tid in zip(job_ids, ["imagen_image", "google_tts", "resize_export"])
    ]
    mock_get_job.side_effect = [
        {"id": jid, "status": "succeeded", "artifact_url": f"path/{jid}.png", "asset_id": f"a-{jid}"}
        for jid in job_ids
    ]

    result = run_studio_flow(flow["id"], "user-1", db=db)  # type: ignore[arg-type]

    assert result["status"] == "succeeded"
    assert len(result["node_jobs"]) == 3
    assert mock_create.call_count == 3
    assert mock_run.call_count == 3
    assert list(mock_create.call_args_list[2].kwargs["params"].keys()) or mock_create.call_args_list[2][1].get("params")

    updated = get_studio_flow(flow["id"], "user-1", db=db)  # type: ignore[arg-type]
    assert updated["last_run"]["status"] == "succeeded"
