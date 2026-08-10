"""Playbooks de livraison par agent — Phase 9 Workspace Dispatch — façade.

Chaque playbook définit :
- pole       : sous-dossier workspace cible
- files      : chemins relatifs au projet (ex: "direction/spec-cursor-prompt.md")
- template   : template markdown avec sections obligatoires
- dod        : checklist Definition of Done (validation humaine)
"""

from __future__ import annotations

from typing import Any

from services.rnd_dispatch_playbook_analytics import PLAYBOOKS as _ANALYTICS_PLAYBOOKS
from services.rnd_dispatch_playbook_app import PLAYBOOKS as _APP_PLAYBOOKS
from services.rnd_dispatch_playbook_comms import PLAYBOOKS as _COMMS_PLAYBOOKS
from services.rnd_dispatch_playbook_direction import PLAYBOOKS as _DIRECTION_PLAYBOOKS
from services.rnd_dispatch_playbook_finance import PLAYBOOKS as _FINANCE_PLAYBOOKS
from services.rnd_dispatch_playbook_gaming import PLAYBOOKS as _GAMING_PLAYBOOKS
from services.rnd_dispatch_playbook_gaming_ship import (
    PLAYBOOKS as _GAMING_PLAYBOOK_OVERRIDES,
)
from services.rnd_dispatch_playbook_hardware import PLAYBOOKS as _HARDWARE_PLAYBOOKS
from services.rnd_dispatch_playbook_hub import PLAYBOOKS as _HUB_PLAYBOOK_OVERRIDES
from services.rnd_dispatch_playbook_innovation import PLAYBOOKS as _INNOVATION_PLAYBOOKS
from services.rnd_dispatch_playbook_robotics_ship import (
    PLAYBOOKS as _ROBOTICS_PLAYBOOK_OVERRIDES,
)
from services.rnd_dispatch_playbook_types import AgentPlaybook  # noqa: F401 — re-export

_PLAYBOOKS: dict[str, AgentPlaybook] = {
    **_DIRECTION_PLAYBOOKS,
    **_COMMS_PLAYBOOKS,
    **_FINANCE_PLAYBOOKS,
    **_APP_PLAYBOOKS,
    **_GAMING_PLAYBOOKS,
    **_INNOVATION_PLAYBOOKS,
    **_HARDWARE_PLAYBOOKS,
    **_ANALYTICS_PLAYBOOKS,
}


def get_playbook(agent_id: str, branch: str | None = None) -> AgentPlaybook | None:
    """Retourne le playbook pour un agent_id; overrides par branche hub/gaming/robotics."""
    branch_norm = (branch or "").strip().lower()
    if branch_norm == "hub" and agent_id in _HUB_PLAYBOOK_OVERRIDES:
        return _HUB_PLAYBOOK_OVERRIDES[agent_id]
    if branch_norm == "gaming" and agent_id in _GAMING_PLAYBOOK_OVERRIDES:
        return _GAMING_PLAYBOOK_OVERRIDES[agent_id]
    if branch_norm == "robotics" and agent_id in _ROBOTICS_PLAYBOOK_OVERRIDES:
        return _ROBOTICS_PLAYBOOK_OVERRIDES[agent_id]
    return _PLAYBOOKS.get(agent_id)


def all_required_files(agent_ids: list[str], branch: str | None = None) -> list[str]:
    """Agrège tous les fichiers requis pour un set d'agents dispatch."""
    files: list[str] = []
    seen: set[str] = set()
    for aid in agent_ids:
        pb = get_playbook(aid, branch=branch)
        if pb:
            for f in pb.files:
                if f not in seen:
                    files.append(f)
                    seen.add(f)
    return files


def _file_full_path(workspace_path: str, slug: str, f: str) -> str:
    """Option A : 'direction/spec.md' -> '{ws}/direction/{slug}/spec.md'"""
    if "/" in f:
        pole, filename = f.split("/", 1)
        return f"{workspace_path}/{pole}/{slug}/{filename}"
    return f"{workspace_path}/{slug}/{f}"


def build_instruction_with_paths(
    agent_id: str,
    dossier_title: str,
    slug: str,
    workspace_path: str,
    context_excerpt: str,
    extra: dict[str, Any] | None = None,
    branch: str | None = None,
) -> str:
    """Construit l'instruction enrichie avec paths workspace pour un agent dispatch.

    Convention Option A : ALNUA/{pole}/{slug}/{filename}
    Les fichiers dans pb.files sont au format 'pole/filename'.
    """
    pb = get_playbook(agent_id, branch=branch)
    if not pb:
        # Fallback générique
        return (
            f"Projet ALNUA : {dossier_title}\n\n"
            f"Workspace : {workspace_path}/\n\n"
            f"Contexte :\n{context_excerpt}\n\n"
            "Produis un livrable markdown structuré et actionnable."
        )

    files_str = "\n".join(
        f"  - {_file_full_path(workspace_path, slug, f)}"
        for f in pb.files
    )
    template_filled = pb.template.replace("{title}", dossier_title)

    extra_context = ""
    if extra:
        extra_context = "\n\nDonnées contextuelles :\n" + "\n".join(
            f"{k}: {v}" for k, v in extra.items() if v
        )

    return (
        f"Projet ALNUA validé par la CEO : {dossier_title}\n"
        f"Pôle : {pb.pole}\n"
        f"Workspace : {workspace_path}/{pb.pole}/{slug}/\n\n"
        f"FICHIERS À PRODUIRE (écriture automatique sur disque) :\n{files_str}\n\n"
        f"Contexte dossier CEO :\n{context_excerpt}\n"
        f"{extra_context}\n\n"
        f"--- TEMPLATE LIVRABLE ---\n"
        f"{template_filled}"
    )
