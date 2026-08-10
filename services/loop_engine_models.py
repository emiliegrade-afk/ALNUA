"""Loop Engine models — Phase C (DEC-024)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

LoopStatus = Literal[
    "PENDING",
    "EXECUTING",
    "EVALUATING",
    "COMPLETED",
    "FAILED",
    "ESCALATED",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class IllegalTransitionError(RuntimeError):
    """FSM refused an illegal state transition."""


class FeedbackRequiredError(ValueError):
    """Rejection without actionable feedback is forbidden."""


@dataclass
class EvalVerdict:
    approved: bool
    feedback: str = ""
    retryable: bool = True
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.approved and not (self.feedback or "").strip():
            raise FeedbackRequiredError(
                "Rejected EvalVerdict MUST include non-empty feedback"
            )


@dataclass
class LoopAttempt:
    iteration: int
    phase: str  # executing | evaluating | approved | rejected | failed
    feedback: str = ""
    detail: str = ""
    started_at: str = field(default_factory=_now_iso)
    finished_at: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "iteration": self.iteration,
            "phase": self.phase,
            "feedback": self.feedback,
            "detail": self.detail,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


@dataclass
class LoopContext:
    """Passed to execute/evaluate — carries append-only feedback history."""

    iteration: int
    feedback_log: list[str] = field(default_factory=list)
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def last_feedback(self) -> str:
        return self.feedback_log[-1] if self.feedback_log else ""

    def feedback_block(self, *, max_chars: int = 4000) -> str:
        if not self.feedback_log:
            return ""
        parts = [
            f"[LOOP FEEDBACK #{i + 1}]\n{fb}"
            for i, fb in enumerate(self.feedback_log)
        ]
        text = "\n\n".join(parts)
        return text[:max_chars]


@dataclass
class LoopState:
    loop_id: str
    status: LoopStatus = "PENDING"
    current_iteration: int = 0
    max_iterations: int = 3
    feedback_log: list[str] = field(default_factory=list)
    attempts: list[LoopAttempt] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    finished_at: str | None = None
    escalate_reason: str = ""

    @staticmethod
    def create(*, max_iterations: int = 3, loop_id: str | None = None) -> LoopState:
        return LoopState(
            loop_id=loop_id or f"loop_{uuid.uuid4().hex[:10]}",
            max_iterations=max(1, int(max_iterations)),
        )

    def advance_to_execution(self) -> None:
        if self.status not in ("PENDING", "EVALUATING"):
            raise IllegalTransitionError(
                f"Cannot EXECUTING from {self.status}"
            )
        self.current_iteration += 1
        if self.current_iteration > self.max_iterations:
            self.status = "ESCALATED"
            self.escalate_reason = (
                f"Max iterations exceeded ({self.max_iterations})"
            )
            self.finished_at = _now_iso()
            raise IllegalTransitionError(self.escalate_reason)
        self.status = "EXECUTING"
        self.attempts.append(
            LoopAttempt(iteration=self.current_iteration, phase="executing")
        )

    def submit_for_review(self) -> None:
        if self.status != "EXECUTING":
            raise IllegalTransitionError(
                f"Cannot EVALUATING from {self.status}"
            )
        self.status = "EVALUATING"
        if self.attempts:
            self.attempts[-1].phase = "evaluating"

    def approve(self, detail: str = "") -> None:
        if self.status != "EVALUATING":
            raise IllegalTransitionError(
                f"Cannot COMPLETED from {self.status}"
            )
        self.status = "COMPLETED"
        self.finished_at = _now_iso()
        if self.attempts:
            self.attempts[-1].phase = "approved"
            self.attempts[-1].detail = detail
            self.attempts[-1].finished_at = self.finished_at

    def reject(self, feedback: str) -> None:
        if self.status != "EVALUATING":
            raise IllegalTransitionError(
                f"Cannot reject from {self.status}"
            )
        fb = (feedback or "").strip()
        if not fb:
            raise FeedbackRequiredError("reject() requires non-empty feedback")
        self.feedback_log.append(fb)
        if self.attempts:
            self.attempts[-1].phase = "rejected"
            self.attempts[-1].feedback = fb
            self.attempts[-1].finished_at = _now_iso()
        # Stay EVALUATING until advance_to_execution or escalate
        # Caller decides next via run_loop

    def fail_fatal(self, reason: str) -> None:
        self.status = "FAILED"
        self.finished_at = _now_iso()
        self.escalate_reason = reason
        if self.attempts:
            self.attempts[-1].phase = "failed"
            self.attempts[-1].feedback = reason
            self.attempts[-1].finished_at = self.finished_at

    def mark_escalated(self, reason: str) -> None:
        self.status = "ESCALATED"
        self.finished_at = _now_iso()
        self.escalate_reason = reason

    def to_dict(self) -> dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "status": self.status,
            "current_iteration": self.current_iteration,
            "max_iterations": self.max_iterations,
            "feedback_log": list(self.feedback_log),
            "attempts": [a.to_dict() for a in self.attempts],
            "created_at": self.created_at,
            "finished_at": self.finished_at,
            "escalate_reason": self.escalate_reason,
        }


@dataclass
class LoopResult:
    success: bool
    status: LoopStatus
    iterations: int
    value: Any = None
    feedback_log: list[str] = field(default_factory=list)
    escalate_reason: str = ""
    loop_id: str = ""
    attempts: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status,
            "iterations": self.iterations,
            "value": self.value,
            "feedback_log": list(self.feedback_log),
            "escalate_reason": self.escalate_reason,
            "loop_id": self.loop_id,
            "attempts": list(self.attempts),
        }
