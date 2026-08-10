"""
services/parallel_runner.py — Exécution parallèle d'agents ALNUA (facade).

Inspiré de oh-my-claude + agent-orchestrator (retry + dependency mgmt).
"""

from __future__ import annotations

from services.parallel_runner_exec import (  # noqa: F401 — re-export
    run_agents_parallel,
    run_agents_parallel_sync,
    run_with_dependencies,
)
from services.parallel_runner_presets import (  # noqa: F401 — re-export
    run_analytics_room,
    run_content_sprint,
)
from services.parallel_runner_progress import get_progress, list_runs  # noqa: F401 — re-export
from services.parallel_runner_types import (  # noqa: F401 — re-export
    AgentResult,
    AgentTask,
    _get_agent_method,
)

__all__ = [
    "AgentResult",
    "AgentTask",
    "_get_agent_method",
    "get_progress",
    "list_runs",
    "run_agents_parallel",
    "run_agents_parallel_sync",
    "run_analytics_room",
    "run_content_sprint",
    "run_with_dependencies",
]
