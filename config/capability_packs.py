"""Capability packs per agent role — Phase E / DEC-026."""

from __future__ import annotations

from config.capability_catalog import CAPABILITIES

# Shared bases
_DEV = frozenset(
    {
        "git:commit",
        "git:push:feature",
        "github:pr:create",
        "coding:worktree",
        "data:write:path",
    }
)
_INTEGRATOR = _DEV | frozenset({"git:merge:staging", "github:pr:merge"})
_DIRECTION = frozenset({"workflow:abort", "data:write:path", "github:pr:create"})
_COMMS = frozenset({"data:write:path", "github:pr:create"})
_SYSTEM = frozenset(
    {
        "system:hotfix",
        "git:merge:main",
        "git:merge:staging",
        "git:commit",
        "git:push:feature",
        "github:pr:create",
        "github:pr:merge",
        "coding:worktree",
        "data:write:path",
        "workflow:abort",
        "mail:send",
    }
)

# Explicit packs — unknown agents get empty pack (fail-closed).
AGENT_CAPABILITY_PACKS: dict[str, frozenset[str]] = {
    # Direction
    "coo": _DIRECTION | frozenset({"workflow:abort", "mail:send"}),
    "spec": _DIRECTION,
    "qa": _DIRECTION,
    "pm": _DIRECTION,
    # App / coding
    "dev_app": _DEV,
    "dev_backend": _DEV,
    "dev_frontend": _DEV,
    "dev_integrator": _INTEGRATOR,
    "coding_coach": frozenset({"data:write:path"}),
    "rnd_product": _DEV,
    # Gaming
    "game_director": _DEV,
    "dev_gaming": _DEV,
    "level_designer": _DEV,
    "ai_programmer": _DEV,
    "environment_artist": _DEV,
    "technical_artist": _DEV,
    "narrative_designer": frozenset({"data:write:path"}),
    "vfx_artist": _DEV,
    "sound_designer": frozenset({"data:write:path"}),
    "qa_gaming": _DIRECTION,
    # Comms
    "marketing": _COMMS,
    "content": _COMMS,
    "content_app": _COMMS,
    "content_gaming": _COMMS,
    "content_robo": _COMMS,
    "content_company": _COMMS,
    "brand": _COMMS,
    "rnd_social": _COMMS,
    "rnd_visual": _COMMS,
    "ads": _COMMS | frozenset({"ads:spend"}),
    # Finance
    "accounting": frozenset({"data:write:path"}),
    "controller": frozenset({"data:write:path", "workflow:abort"}),
    # Hardware
    "hardware": _DEV,
    "embedded_dev": _DEV,
    "vision_ai": _DEV,
    "electronics": _DEV,
    "firmware": _DEV,
    "mechanical": _DEV,
    "industrial_design": frozenset({"data:write:path"}),
    "qa_robot": _DIRECTION,
    "safety": _DIRECTION,
    "simulation": _DEV,
    # Analytics / secretary
    "analyst_business": frozenset({"data:write:path"}),
    "analyst_data": frozenset({"data:write:path"}),
    "secretary": frozenset({"mail:send", "data:write:path"}),
    # R&D lab
    "brainstorm": frozenset({"data:write:path"}),
    "rnd_agent": frozenset({"data:write:path", "github:pr:create"}),
    "rnd_dossier": frozenset({"data:write:path"}),
    "rnd_ceo": _DIRECTION,
    "rnd_committee": frozenset({"data:write:path"}),
    # System / pipelines (not personas)
    "fix_pipeline": _SYSTEM,
    "coding_pipeline": _SYSTEM - frozenset({"git:merge:main"}) | frozenset({"git:merge:staging"}),
    "gh_issues": frozenset({"github:pr:create", "github:pr:merge", "git:merge:staging", "data:write:path"}),
    "system": _SYSTEM,
    "review_chain": frozenset({"data:write:path", "workflow:abort"}),
    # MCP clients (Cursor) — fail-closed: no spend / merge / mail by default
    "cursor": frozenset({"data:write:path"}),
    "mcp_client": frozenset({"data:write:path"}),
}


def normalize_agent_id(agent_id: str) -> str:
    aid = (agent_id or "").strip().lower()
    if aid.endswith("_agent") and aid != "coo_agent":
        aid = aid[: -len("_agent")]
    if aid == "coo_agent":
        aid = "coo"
    return aid


def pack_for(agent_id: str) -> frozenset[str]:
    return AGENT_CAPABILITY_PACKS.get(normalize_agent_id(agent_id), frozenset())


def agent_has_capability(agent_id: str, capability: str) -> bool:
    cap = (capability or "").strip()
    if cap not in CAPABILITIES:
        return False
    return cap in pack_for(agent_id)


def list_packs() -> dict[str, list[str]]:
    return {k: sorted(v) for k, v in sorted(AGENT_CAPABILITY_PACKS.items())}
