"""Review Chain models — Phase D / DEC-025."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

GateId = Literal["AUTO", "BOARD", "POLICY", "INTEGRATE", "DONE"]
GateOutcome = Literal["pass", "fail", "skip", "human_required"]
ChainStatus = Literal[
    "PENDING",
    "RUNNING",
    "APPROVED",
    "REJECTED",
    "A_VERIFIER",
    "BLOCKED_POLICY",
    "INTEGRATE_FAILED",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class GateResult:
    gate: GateId
    outcome: GateOutcome
    detail: str = ""
    feedback: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate": self.gate,
            "outcome": self.outcome,
            "detail": self.detail,
            "feedback": self.feedback,
            "meta": dict(self.meta),
        }


@dataclass
class ReviewChainResult:
    chain_id: str
    status: ChainStatus
    gates: list[GateResult] = field(default_factory=list)
    feedback_log: list[str] = field(default_factory=list)
    merge_mode: str = ""  # auto | human_required | deny
    integrate: dict[str, Any] | None = None
    started_at: str = ""
    finished_at: str = ""

    @property
    def approved(self) -> bool:
        return self.status == "APPROVED"

    @property
    def needs_human(self) -> bool:
        return self.status == "A_VERIFIER" or self.merge_mode == "human_required"

    def to_dict(self) -> dict[str, Any]:
        return {
            "chain_id": self.chain_id,
            "status": self.status,
            "approved": self.approved,
            "needs_human": self.needs_human,
            "gates": [g.to_dict() for g in self.gates],
            "feedback_log": list(self.feedback_log),
            "merge_mode": self.merge_mode,
            "integrate": self.integrate,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


def new_chain_id() -> str:
    return f"rc_{uuid4().hex[:12]}"
