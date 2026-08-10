"""Capability catalog — Phase E / DEC-026 (Capability ≠ Skill)."""

from __future__ import annotations

# Stable IDs — do not rename lightly (Trust Graph + packs depend on them).
CAPABILITIES: dict[str, str] = {
    "git:commit": "Create local git commits",
    "git:push:feature": "Push feature branches (not protected tips)",
    "git:merge:staging": "Merge into staging",
    "git:merge:main": "Merge into main/master",
    "github:pr:create": "Open GitHub pull requests",
    "github:pr:merge": "Merge GitHub pull requests via gh",
    "coding:worktree": "Create or use coding worktrees",
    "data:write:path": "Write hub runtime data paths",
    "ads:spend": "Spend advertising budget",
    "mail:send": "Send email on behalf of ALNUA",
    "workflow:abort": "Abort workflow / mission runs",
    "system:hotfix": "System hotfix merge path (fix_pipeline)",
}


def known_capability(capability: str) -> bool:
    return (capability or "").strip() in CAPABILITIES


def list_capabilities() -> list[dict[str, str]]:
    return [{"id": k, "description": v} for k, v in sorted(CAPABILITIES.items())]
