"""Context Engine — compile L1→L4 prompt layers (DEC-027 / Phase F)."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class ContextBundle:
    agent_id: str
    task: str
    task_id: str | None = None
    room: str | None = None
    l1: str = ""
    l2: str = ""
    l3: str = ""
    l4: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def as_block(self) -> str:
        return "".join(p for p in (self.l1, self.l2, self.l3, self.l4) if p)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "task": self.task[:200],
            "task_id": self.task_id,
            "room": self.room,
            "layers": {
                "l1": bool(self.l1),
                "l2": bool(self.l2),
                "l3": bool(self.l3),
                "l4": bool(self.l4),
            },
            "block_chars": len(self.as_block()),
            "meta": self.meta,
        }


def context_engine_enabled() -> bool:
    try:
        from config.settings import get_settings

        return bool(getattr(get_settings(), "context_engine_enabled", True))
    except Exception:
        return True


def compile_context(
    agent_id: str,
    task: str,
    *,
    task_id: str | None = None,
    loop_feedback: str | None = None,
    include_library: bool = True,
) -> ContextBundle:
    """Assemble stratified context. Degrades silently per layer."""
    from config.agent_models import memory_agent_id

    aid = memory_agent_id(agent_id)
    room: str | None = None
    try:
        from config.agent_personas import get_room

        room = get_room(aid) or get_room(agent_id)
    except Exception:
        room = None

    bundle = ContextBundle(agent_id=aid, task=task or "", task_id=task_id, room=room)
    if not context_engine_enabled():
        # Legacy path: L3 + library only
        try:
            from skills.skill_agent_learning_context import get_learning_context, get_library_context

            bundle.l3 = get_learning_context(aid, task)
            if include_library:
                bundle.l2 = get_library_context(aid, task)
        except Exception:
            pass
        bundle.meta["mode"] = "legacy_disabled"
        return bundle

    try:
        from config.enterprise_policies import l1_policies_block

        bundle.l1 = l1_policies_block()
    except Exception as exc:
        logger.debug("L1 compile failed: %s", exc)

    try:
        from config.bureau_standards import l2_standards_block
        from services.collective_learning import l2_collective_block

        std = l2_standards_block(room)
        coll = l2_collective_block(room)
        lib = ""
        if include_library:
            from skills.skill_agent_learning_context import get_library_context

            lib = get_library_context(aid, task)
        bundle.l2 = std + coll + lib
    except Exception as exc:
        logger.debug("L2 compile failed: %s", exc)

    try:
        from skills.skill_agent_learning_context import get_learning_context

        bundle.l3 = get_learning_context(aid, task)
    except Exception as exc:
        logger.debug("L3 compile failed: %s", exc)

    try:
        from services.working_memory import l4_block

        bundle.l4 = l4_block(task_id, loop_feedback=loop_feedback)
    except Exception as exc:
        logger.debug("L4 compile failed: %s", exc)

    bundle.meta["mode"] = "l1_l4"
    return bundle


def compile_context_block(
    agent_id: str,
    task: str,
    *,
    task_id: str | None = None,
    loop_feedback: str | None = None,
    include_library: bool = True,
) -> str:
    return compile_context(
        agent_id,
        task,
        task_id=task_id,
        loop_feedback=loop_feedback,
        include_library=include_library,
    ).as_block()


__all__ = [
    "ContextBundle",
    "compile_context",
    "compile_context_block",
    "context_engine_enabled",
]
