"""MCP / HTTP route → capability map (DEC-026 progressive MCP guard).

Only mutating routes listed here are enforced when an MCP client identifies
itself via X-MCP-Agent. Unmapped routes stay on call-site guards.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class McpRouteRule:
    """Match FastAPI paths that MCP tools can invoke."""

    capability: str
    methods: frozenset[str]
    path_exact: str | None = None
    path_suffix: str | None = None
    path_contains: str | None = None


# Ordered — first match wins.
MCP_ROUTE_RULES: tuple[McpRouteRule, ...] = (
    McpRouteRule(
        capability="ads:spend",
        methods=frozenset({"POST"}),
        path_exact="/agents/ads/create-campaign",
    ),
    McpRouteRule(
        capability="github:pr:create",
        methods=frozenset({"POST"}),
        path_exact="/agents/dev-integrator/open-pr",
    ),
    McpRouteRule(
        capability="git:merge:staging",
        methods=frozenset({"POST"}),
        path_exact="/agents/dev-integrator/integrate",
    ),
    McpRouteRule(
        capability="workflow:abort",
        methods=frozenset({"POST"}),
        path_suffix="/abort",
        path_contains="/missions/",
    ),
    McpRouteRule(
        capability="workflow:abort",
        methods=frozenset({"POST"}),
        path_suffix="/abort",
        path_contains="/workflows/runs/",
    ),
    McpRouteRule(
        capability="coding:worktree",
        methods=frozenset({"POST"}),
        path_contains="/pipeline/run",
    ),
)


def match_mcp_capability(method: str, path: str) -> str | None:
    """Return required capability for this HTTP call, or None if unmapped."""
    m = (method or "").upper()
    p = (path or "").split("?", 1)[0]
    if p.startswith("/v1/"):
        p = p[3:]
    for rule in MCP_ROUTE_RULES:
        if m not in rule.methods:
            continue
        if rule.path_exact is not None:
            if p == rule.path_exact:
                return rule.capability
            continue
        if rule.path_suffix and not p.endswith(rule.path_suffix):
            continue
        if rule.path_contains and rule.path_contains not in p:
            continue
        if rule.path_suffix or rule.path_contains:
            return rule.capability
    return None


def list_mcp_route_rules() -> list[dict[str, object]]:
    return [
        {
            "capability": r.capability,
            "methods": sorted(r.methods),
            "path_exact": r.path_exact,
            "path_suffix": r.path_suffix,
            "path_contains": r.path_contains,
        }
        for r in MCP_ROUTE_RULES
    ]
