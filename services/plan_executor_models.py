"""Plan executor — dataclasses for COO execution plans."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionStep:
    step_id: str
    description: str
    agent_id: str
    method: str
    kwargs: dict[str, Any] = field(default_factory=dict)
    depends_on: list[str] = field(default_factory=list)
    award_points: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "description": self.description,
            "agent_id": self.agent_id,
            "method": self.method,
            "depends_on": self.depends_on,
        }


@dataclass
class StepResult:
    step_id: str
    agent_id: str
    description: str
    success: bool
    result: Any
    error: str | None
    duration_ms: int
    retries: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "agent_id": self.agent_id,
            "description": self.description,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "duration_ms": self.duration_ms,
            "retries": self.retries,
        }


@dataclass
class ExecutionPlan:
    title: str
    steps: list[ExecutionStep]
    context: str = ""
    plan_id: str = field(default_factory=lambda: f"plan_{int(time.time())}")
    objective: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "title": self.title,
            "objective": self.objective,
            "total_steps": len(self.steps),
            "steps": [s.to_dict() for s in self.steps],
        }
