"""Shared helpers for R&D dispatch executor — agent IDs, logs, text extraction."""

from __future__ import annotations

import logging
import os
from typing import Any

from services.agent_pipeline_registry import LOG_NAME_TO_AGENT_ID
from services.rnd_ceo_package import resolve_branch
from services.rnd_dispatch_playbooks import build_instruction_with_paths
from services.rnd_schemas import RndDossierOut

logger = logging.getLogger(__name__)

# dispatch matrix agent_id -> pipeline agent_id
_DISPATCH_AGENT_ALIASES: dict[str, str] = {
    "pm_agent": "pm",
    "spec_agent": "spec",
    "qa_agent": "qa",
    "marketing_agent": "marketing",
    "accountant_agent": "accounting",
    "accounting": "accounting",
    "dev_app_agent": "dev_app",
    "dev_app": "dev_app",
    "dev_backend_agent": "dev_backend",
    "dev_gaming": "dev_gaming",
    "game_director": "game_director",
    "content_agent": "content",
    "content": "content",
    "hardware_agent": "hardware",
    "hardware": "hardware",
    "embedded_dev": "embedded_dev",
    "coo_agent": "coo",
    "coo": "coo",
}


def normalize_dispatch_agent_id(raw: str) -> str:
    key = (raw or "").strip()
    return _DISPATCH_AGENT_ALIASES.get(key, key.replace("_agent", ""))


def workspace_root_str() -> str:
    """Retourne ALNUA_WORKSPACE root comme string (ne trigger pas config si env set)."""
    raw = os.environ.get("ALNUA_WORKSPACE", "").strip()
    if raw:
        return raw
    try:
        from config.paths import get_alnua_workspace

        return str(get_alnua_workspace())
    except Exception:
        import platform

        if platform.system() == "Windows":
            return "C:/Dev/ALUNA"
        from pathlib import Path as _P

        return str(_P.home() / "Dev" / "ALNUA")


def task_instruction(
    dossier: RndDossierOut,
    row: dict[str, Any],
    package: dict[str, Any],
    agent_id: str,
    workspace_path: str,
) -> str:
    """Instruction enrichie avec paths workspace et template playbook."""
    excerpt = (package.get("markdown") or dossier.one_pager_md or "")[:3000]

    extra: dict[str, Any] = {}
    if agent_id == "accounting":
        extra["finance_json"] = dossier.finance_json or {}
    if agent_id in ("pm", "spec"):
        extra["pole"] = row.get("pole", "")
        extra["deliverables_attendus"] = ", ".join(row.get("deliverables") or [])

    return build_instruction_with_paths(
        agent_id=agent_id,
        dossier_title=dossier.title,
        slug=dossier.slug or dossier.id,
        workspace_path=workspace_path,
        context_excerpt=excerpt,
        extra=extra or None,
        branch=resolve_branch(dossier),
    )


def agent_log_name(agent_id: str) -> str:
    for log_name, openroom_id in LOG_NAME_TO_AGENT_ID.items():
        if openroom_id == agent_id and log_name.endswith("_agent"):
            return log_name
    return f"{agent_id}_agent" if agent_id not in LOG_NAME_TO_AGENT_ID else agent_id


def write_agent_log(
    db: Any,
    *,
    agent_id: str,
    action: str,
    status: str,
    summary: str,
    project_id: str | None,
) -> None:
    try:
        db.insert(
            "agent_logs",
            {
                "agent_name": agent_log_name(agent_id),
                "action": action,
                "status": status,
                "project_id": project_id,
                "input_summary": summary[:4000],
                "output_summary": summary[:4000],
            },
        )
    except Exception as exc:
        logger.warning("agent log failed %s: %s", agent_id, exc)


def extract_text_output(result: Any) -> str:
    """Extrait le contenu textuel d'un resultat agent (str, dict, CrewAI output)."""
    if isinstance(result, str):
        return result
    if hasattr(result, "raw"):
        return str(result.raw)
    if isinstance(result, dict):
        for key in (
            "content",
            "output",
            "result",
            "text",
            "markdown",
            "cursor_prompt",
            "advice",
            "message",
            "summary",
            "report",
        ):
            if isinstance(result.get(key), str) and result[key].strip():
                return result[key]
        return str(result)
    return str(result) if result is not None else ""


# Backward-compatible private aliases for tests/scripts importing underscore names.
_extract_text_output = extract_text_output
