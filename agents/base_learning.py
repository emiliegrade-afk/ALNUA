"""Learning wrapper — Mem0 + competition + event bus hooks."""

from __future__ import annotations

import asyncio
import traceback
from typing import Any


def run_with_learning(
    agent_id: str,
    task: str,
    fn,
    *args,
    **kwargs,
) -> Any:
    """
    Wrapper universel : exécute fn(*args, **kwargs) puis déclenche
    l'apprentissage en arrière-plan selon le résultat.

    Usage dans n'importe quel agent :
        result = run_with_learning("marketing_agent", "Rédiger post", self.write_post, topic)

    Tous les agents héritent de cette fonction — aucun code dupliqué.
    """
    from skills.skill_agent_learning import is_task_failure

    try:
        result = fn(*args, **kwargs)
        outcome = str(result)[:600] if result else "Tâche complétée sans output"
        try:
            from skills.skill_agent_learning import learn_from_outcome
            learn_from_outcome(
                agent_id=agent_id,
                task=task,
                outcome=outcome,
                success=not is_task_failure(outcome),
            )
        except Exception:
            pass
        try:
            from services.competition import add_points
            add_points(agent_id, "task_completed", note=f"{task[:80]}")
        except Exception:
            pass
        try:
            from services.event_bus import emit

            emit(
                "task_completed",
                {"task": task[:200], "agent_id": agent_id},
                source_agent=agent_id,
            )
        except Exception:
            pass
        return result
    except Exception as exc:
        error_str = f"{type(exc).__name__}: {exc}\n{traceback.format_exc()[-500:]}"
        try:
            from skills.skill_agent_learning import learn_from_failure
            learn_from_failure(agent_id=agent_id, task=task, error=error_str)
        except Exception:
            pass
        try:
            from services.event_bus import emit

            emit(
                "task_failed",
                {
                    "task": task[:200],
                    "agent_id": agent_id,
                    "error": error_str[:300],
                },
                source_agent=agent_id,
            )
        except Exception:
            pass
        raise


async def run_with_learning_async(
    agent_id: str,
    task: str,
    fn,
    *args,
    **kwargs,
) -> Any:
    """Async variant — runs sync fn in thread pool, preserves learning hooks."""
    return await asyncio.to_thread(run_with_learning, agent_id, task, fn, *args, **kwargs)
