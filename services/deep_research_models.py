"""Deep research — dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ResearchRound:
    round_num: int
    query: str
    findings: list[str]
    sources_mentioned: list[str]
    confidence: str    # "high" | "medium" | "low"
    gaps_identified: list[str]

    def to_dict(self) -> dict[str, Any]:
        return {
            "round": self.round_num,
            "query": self.query,
            "findings": self.findings,
            "sources_mentioned": self.sources_mentioned,
            "confidence": self.confidence,
            "gaps_identified": self.gaps_identified,
        }


@dataclass
class ResearchReport:
    query: str
    agent_id: str
    rounds_completed: int
    executive_summary: str
    key_findings: list[dict[str, str]]   # [{finding, confidence, source}]
    verified_claims: list[str]
    unverified_claims: list[str]
    knowledge_gaps: list[str]
    recommended_actions: list[str]
    rounds_history: list[ResearchRound]
    depth: str   # "quick" | "standard" | "deep"
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "agent_id": self.agent_id,
            "rounds_completed": self.rounds_completed,
            "depth": self.depth,
            "executive_summary": self.executive_summary,
            "key_findings": self.key_findings,
            "verified_claims": self.verified_claims,
            "unverified_claims": self.unverified_claims,
            "knowledge_gaps": self.knowledge_gaps,
            "recommended_actions": self.recommended_actions,
            "rounds_history": [r.to_dict() for r in self.rounds_history],
            "generated_at": self.generated_at,
        }
