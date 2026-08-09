"""
Coding facade — single public entry map for Hub coding engines.

Two engines coexist on purpose (do not merge blindly):

| Engine | Module | When to use |
|--------|--------|-------------|
| Hub / CLI coding | `skills.skill_coding_agent` | Dev agents, Academy pipeline, worktree+PR (`execute_coding_task`) |
| Internal fix | `skills.skill_code_agent` | Bug watchdog / fix_pipeline (`fix_bug`) — OpenRouter + gitpython |

Legacy standalone `skill_aider` / `skill_openhands` modules were removed in Phase D
(Audit 002 BUG-014). Aider remains an optional *backend* inside
`skill_coding_agent` when `CODING_BACKEND=aider`.
"""

from __future__ import annotations

from typing import Any


def execute_hub_coding_task(spec: dict[str, Any]) -> dict[str, Any]:
    """Worktree + Claude/Aider CLI path (dev agents / Academy)."""
    from skills.skill_coding_agent import execute_coding_task

    return execute_coding_task(spec)


def fix_bug_internal(
    *,
    error_message: str,
    error_context: str = "",
    repo_path: str = "",
    github_repo: str | None = None,
    hint_files: list[str] | None = None,
    agent_id: str = "dev_app",
    dry_run: bool = False,
) -> dict[str, Any]:
    """Watchdog / fix_pipeline path (no external Aider/OpenHands process)."""
    from skills.skill_code_agent import fix_bug

    return fix_bug(
        error_message=error_message,
        error_context=error_context,
        repo_path=repo_path,
        github_repo=github_repo,
        hint_files=hint_files,
        agent_id=agent_id,
        dry_run=dry_run,
    )
