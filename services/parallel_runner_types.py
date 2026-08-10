"""Parallel runner — task/result types and agent method resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


def _get_agent_method(agent_id: str, method_name: str) -> Callable:
    """Résout dynamiquement la méthode d'un agent par son ID."""
    from services.agent_pipeline_registry import get_agent_method

    return get_agent_method(agent_id, method_name)


@dataclass
class AgentTask:
    """Définition d'une tâche agent pour l'exécution parallèle."""
    agent_id: str
    method: str
    kwargs: dict[str, Any] = field(default_factory=dict)
    task_label: str = ""
    award_points: bool = True
    max_retries: int = 2
    depends_on: list[str] = field(default_factory=list)
    # Phase A isolation (DEC-022) — optional explicit resource keys / repo
    lock_keys: list[str] = field(default_factory=list)
    repo_slug: str = ""
    repo_path: str = ""

    @property
    def label(self) -> str:
        return self.task_label or f"{self.agent_id}.{self.method}"


@dataclass
class AgentResult:
    """Résultat d'une tâche agent exécutée en parallèle."""
    agent_id: str
    method: str
    task_label: str
    success: bool
    result: Any = None
    error: str | None = None
    duration_ms: int = 0
    points_awarded: int = 0
    retries: int = 0
