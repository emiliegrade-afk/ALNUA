"""Parallel runner — progress registry."""

from __future__ import annotations

from typing import Any

_TASK_PROGRESS: dict[str, dict[str, Any]] = {}


def get_progress(run_id: str) -> dict[str, Any]:
    """Retourne l'état de progression d'un run parallèle."""
    return _TASK_PROGRESS.get(run_id, {"error": "run_id not found"})


def list_runs(limit: int = 20) -> list[dict[str, Any]]:
    """Liste les derniers runs (les plus récents en premier)."""
    runs = sorted(
        _TASK_PROGRESS.values(),
        key=lambda r: r.get("started_at", 0),
        reverse=True,
    )
    return runs[:limit]
