"""Kick off real agent work after R&D CEO dispatch (plan_executor).

Phase 9 — Workspace dispatch :
- Chaque agent produit un livrable concret ecrit sur disque (ALNUA_WORKSPACE)
- Convention Option A : ALNUA/{pole}/{slug}/{filename}
- Playbooks definissent fichiers attendus + templates
- Manifest JSON trace les statuts par agent
- Validation finale : tous les fichiers requis doivent exister AVANT de marquer success
  dans agent_logs (item 5) et dans le manifest

Corrections Round 2 :
- Item 2 : spec utilise generate_and_write_dispatch + ticket Supabase cree avant
- Item 4 : PM — verifie ticket + roadmap en base apres handle_instruction
- Item 5 : agent_logs success SEULEMENT apres validate_deliverables() par agent
- Item 8 : persist workspace_validation sur rnd_dossier en fin d'execution
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone
from typing import Any

from services.plan_executor import execute_plan  # noqa: F401 — re-export for test patches
from services.rnd_schemas import RndDossierOut

from services.rnd_dispatch_executor_helpers import (
    _extract_text_output,
    extract_text_output,
    normalize_dispatch_agent_id,
    write_agent_log,
)
from services.rnd_dispatch_executor_plan import build_dispatch_execution_plan
from services.rnd_dispatch_executor_run import run_dispatch_execution

logger = logging.getLogger(__name__)

__all__ = [
    "build_dispatch_execution_plan",
    "execute_plan",
    "normalize_dispatch_agent_id",
    "run_dispatch_execution",
    "start_dispatch_execution_background",
    "_extract_text_output",
    "extract_text_output",
]


def start_dispatch_execution_background(
    dossier: RndDossierOut,
    matrix: list[dict[str, Any]],
    package: dict[str, Any],
    project_id: str | None,
    db: Any,
    *,
    on_complete: Any | None = None,
) -> str:
    """Fire-and-forget thread — returns run label."""
    run_id = f"dispatch_{dossier.slug or dossier.id}_{int(datetime.now(timezone.utc).timestamp())}"

    def _worker() -> None:
        try:
            run_result = run_dispatch_execution(dossier, matrix, package, project_id, db)
            if on_complete:
                on_complete(run_result)
        except Exception as exc:
            logger.exception("dispatch execution failed for %s: %s", dossier.title, exc)
            write_agent_log(
                db,
                agent_id="coo",
                action="rnd_dispatch_execute",
                status="error",
                summary=str(exc)[:4000],
                project_id=project_id,
            )

    threading.Thread(
        target=_worker,
        daemon=True,
        name=run_id,
    ).start()
    return run_id
