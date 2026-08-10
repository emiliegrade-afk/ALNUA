"""MCP PermissionGuard progressive interception (DEC-026)."""

from __future__ import annotations

import pytest

from config.mcp_capability_routes import match_mcp_capability
from services.mcp_permission_guard import (
    enforce_mcp_http,
    extract_mcp_agent,
    is_mcp_identified_request,
)


@pytest.fixture
def mcp_guard_env(tmp_path, monkeypatch: pytest.MonkeyPatch):
    path = tmp_path / "trust_graph.jsonl"
    monkeypatch.setattr("services.trust_graph._STORE", path)
    monkeypatch.setenv("PERMISSION_GUARD_ENABLED", "1")
    monkeypatch.setenv("PERMISSION_GUARD_MCP_ENABLED", "1")
    try:
        from config.settings import get_settings

        get_settings.cache_clear()
    except Exception:
        pass
    return path


def test_match_mcp_routes() -> None:
    assert match_mcp_capability("POST", "/agents/ads/create-campaign") == "ads:spend"
    assert match_mcp_capability("POST", "/agents/dev-integrator/open-pr") == "github:pr:create"
    assert match_mcp_capability("POST", "/missions/mis_1/abort") == "workflow:abort"
    assert match_mcp_capability("POST", "/workflows/runs/wf_1/abort") == "workflow:abort"
    assert match_mcp_capability("POST", "/pipeline/run/42") == "coding:worktree"
    assert match_mcp_capability("GET", "/agents/ads/create-campaign") is None
    assert match_mcp_capability("POST", "/health") is None


def test_extract_mcp_agent() -> None:
    assert extract_mcp_agent({"X-MCP-Agent": "coo"}) == "coo"
    assert extract_mcp_agent({"X-MCP-Client": "1"}) == "cursor"
    assert extract_mcp_agent({}) is None
    assert is_mcp_identified_request({"X-MCP-Agent": "ads"}) is True
    assert is_mcp_identified_request({}) is False


def test_enforce_denies_cursor_on_ads(mcp_guard_env) -> None:
    denied = enforce_mcp_http(
        "POST",
        "/agents/ads/create-campaign",
        {"X-MCP-Agent": "cursor"},
    )
    assert denied is not None
    assert denied["allowed"] is False
    assert denied["capability"] == "ads:spend"


def test_enforce_allows_ads_agent(mcp_guard_env) -> None:
    denied = enforce_mcp_http(
        "POST",
        "/agents/ads/create-campaign",
        {"X-MCP-Agent": "ads"},
    )
    assert denied is None


def test_enforce_skips_without_mcp_header(mcp_guard_env) -> None:
    # Non-MCP traffic: call-site guards only
    assert (
        enforce_mcp_http("POST", "/agents/ads/create-campaign", {}) is None
    )


def test_enforce_coo_abort(mcp_guard_env) -> None:
    assert (
        enforce_mcp_http(
            "POST",
            "/missions/mis_abc/abort",
            {"X-MCP-Agent": "coo"},
        )
        is None
    )
    denied = enforce_mcp_http(
        "POST",
        "/missions/mis_abc/abort",
        {"X-MCP-Agent": "dev_app"},
    )
    assert denied is not None


def test_mcp_routes_api(hub_client, mcp_guard_env) -> None:
    from tests.conftest import HUB_HEADERS

    r = hub_client.get("/mcp-capability-routes", headers=HUB_HEADERS)
    assert r.status_code == 200
    rules = r.json()["rules"]
    assert any(x["capability"] == "ads:spend" for x in rules)


def test_mcp_middleware_403(hub_client, mcp_guard_env) -> None:
    from tests.conftest import HUB_HEADERS

    headers = {**HUB_HEADERS, "X-MCP-Agent": "cursor"}
    r = hub_client.post(
        "/agents/ads/create-campaign",
        headers=headers,
        json={
            "brief": "Test campaign brief for MCP guard denial path",
            "platform": "meta",
            "budget_usd": 10,
            "objective": "traffic",
            "audience": "test",
        },
    )
    assert r.status_code == 403
    body = r.json()
    assert "capability" in (body.get("detail") or "").lower() or "permission" in body
