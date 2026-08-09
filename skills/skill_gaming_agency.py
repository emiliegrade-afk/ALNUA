"""Gaming studio agency — Claude Code on the local UE5.8 project (DEC-020).

Gives Gaming agents PC agency like Claude Code: edit/write/bash inside an
isolated worktree of UE_PROJECT_PATH / REPO_PATH_GAMING. Not full desktop GUI
control (Cowork-style mouse) — that stays out of scope.

Editor-side actions (PIE, Blueprint tools) go through skill_ue58.call_tool when
the UE5.8 server is up.
"""
from __future__ import annotations

import logging
import os
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

STUDIO_AGENTS: frozenset[str] = frozenset(
    {
        "dev_gaming",
        "ai_programmer",
        "technical_artist",
        "vfx_artist",
        "game_director",
        "level_designer",
        "environment_artist",
        "narrative_designer",
        "sound_designer",
        "qa_gaming",
    }
)

_AGENCY_NOT_CONFIGURED = (
    "Projet UE non configuré — définir UE_PROJECT_PATH ou REPO_PATH_GAMING "
    "(chemin local du projet Unreal / repo gaming)."
)


def get_ue_project_path() -> Path | None:
    raw = (
        os.getenv("UE_PROJECT_PATH", "").strip()
        or os.getenv("REPO_PATH_GAMING", "").strip()
    )
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


def ue_project_ready() -> tuple[bool, str]:
    path = get_ue_project_path()
    if path is None:
        return False, _AGENCY_NOT_CONFIGURED
    if not path.is_dir():
        return False, f"Chemin projet UE introuvable : {path}"
    return True, str(path)


def _claude_cli_available() -> bool:
    return shutil.which("claude") is not None


def agency_status() -> dict[str, Any]:
    """Honest status for console / agents — never pretends the project exists."""
    ready, detail = ue_project_ready()
    from skills.skill_ue58 import ue58_health

    ue58 = ue58_health()
    backend = os.getenv("CODING_BACKEND", "hub").strip().lower()
    return {
        "ok": ready,
        "configured": ready,
        "project_path": detail if ready else None,
        "error": None if ready else detail,
        "claude_code_cli": _claude_cli_available(),
        "coding_backend": backend,
        "studio_agents": sorted(STUDIO_AGENTS),
        "ue58": {
            "configured": ue58.get("configured"),
            "connected": ue58.get("connected"),
            "error": ue58.get("error"),
        },
        "mode": {
            "code_on_pc": "Claude Code / hub coding agent in git worktree of UE project",
            "editor": "UE5.8 server tools/call when connected (SPEC_UE58_BRIDGE)",
            "not_included": "Full Windows desktop GUI control (mouse/windows) — out of scope",
        },
    }


def _slug(title: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", (title or "task").lower()).strip("-")
    return (s[:40] or "task")


def run_studio_task(
    *,
    agent_id: str,
    title: str,
    description: str,
    files_to_create: list[str] | None = None,
    files_to_modify: list[str] | None = None,
) -> dict[str, Any]:
    """
    Run Claude Code / coding pipeline against the local UE project.

    Same trust model as Academy coding: worktree isolation + CODING_* settings.
    Project path must be a git repo (Claude Code / hub agent expect git).
    """
    from config.agent_models import normalize_agent_id
    from skills.skill_coding_agent import execute_coding_task

    agent_id = normalize_agent_id(agent_id)
    if agent_id not in STUDIO_AGENTS:
        return {
            "ok": False,
            "success": False,
            "error": f"Agent '{agent_id}' non autorisé pour l'agency studio Gaming.",
        }

    ready, detail = ue_project_ready()
    if not ready:
        return {"ok": False, "success": False, "configured": False, "error": detail}

    project = Path(detail)
    if not (project / ".git").exists():
        return {
            "ok": False,
            "success": False,
            "configured": True,
            "error": (
                f"Le projet UE doit être un dépôt git (pas de .git dans {project}). "
                "Initialise git ou pointe UE_PROJECT_PATH vers le repo."
            ),
        }

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    branch = f"feat/ue58-{agent_id}-{_slug(title)}-{stamp}"

    spec: dict[str, Any] = {
        "task_id": f"ue58-{agent_id}-{stamp}",
        "title": title[:200],
        "description": (
            f"[UE5.8 / Gaming agency — agent {agent_id}]\n\n"
            f"{description}\n\n"
            "CONTRAINTES :\n"
            "- Projet Unreal Engine 5.8 sur cette machine.\n"
            "- Toujours préciser Blueprint vs C++ et pourquoi.\n"
            "- Respecter conventions UE (U/A/F/E, Content/, Source/).\n"
            "- Ne pas toucher aux secrets (.env, credentials).\n"
            "- Preférer changements petits et testables (PIE si pertinent).\n"
        ),
        "files_to_create": files_to_create or [],
        "files_to_modify": files_to_modify or [],
        "tests_to_pass": [],
        "repo_path": str(project),
        "branch_name": branch,
        "pr_title": f"feat(ue58): {title[:120]}",
        "pr_body": f"Studio agency run by `{agent_id}`.\n\n{description[:1500]}",
        "agent_id": agent_id,
    }

    logger.info(
        "[GamingAgency] run agent=%s path=%s title=%s",
        agent_id,
        project,
        title[:80],
    )
    result = execute_coding_task(spec)
    return {
        "ok": bool(result.get("success")),
        "success": bool(result.get("success")),
        "configured": True,
        "agent_id": agent_id,
        "project_path": str(project),
        "branch": result.get("branch"),
        "pr_url": result.get("pr_url"),
        "commit_sha": result.get("commit_sha"),
        "claude_output": (result.get("claude_output") or "")[:8000],
        "error": result.get("error"),
        "backend": result.get("backend"),
    }


def invoke_editor_tool(tool_id: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Invoke a capability on the UE5.8 server (editor-side agency)."""
    from skills.skill_ue58 import call_tool

    return call_tool(tool_id, arguments or {})
