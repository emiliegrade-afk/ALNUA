"""QA Gaming Agent — Tomás Freitas, tests gameplay ALNUA Gaming."""
from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt
from skills.skill_langfuse import trace_agent


class QaGamingAgent(AgentBase):
    AGENT_NAME = "qa_gaming"
    SYSTEM_PROMPT = get_system_prompt("qa_gaming")

    @trace_agent("qa_gaming")
    def build_test_plan(
        self,
        feature_name: str,
        game: str,
        build_version: str = "",
        risk_areas: str = "",
    ) -> dict[str, Any]:
        """Construit un plan de test pour une feature ou un build avant validation."""
        prompt = f"""Construis un plan de test pour {game}.
Feature/build : {feature_name}
Version : {build_version or 'non précisée'}
Zones à risque signalées : {risk_areas or 'Aucune signalée — couverture standard'}

Réponds en JSON :
{{
  "feature": "{feature_name}",
  "build_version": "{build_version}",
  "test_cases": [{{ "id": 1, "scenario": "string", "expected": "string", "priority": "critical|high|medium|low" }}],
  "regression_focus": ["Zones à re-tester en priorité"],
  "known_risk_areas": ["string"],
  "exit_criteria": "Critère de fin de test (ex: 0 bug bloquant, N bugs mineurs acceptés)"
}}"""
        return self.run_json_task(
            action="build_test_plan",
            prompt=prompt,
            learning_key=feature_name,
            input_summary=f"{game} | {feature_name} | {build_version}",
            output_summary=lambda r: f"{len(r.get('test_cases', []))} cas de test",
            temperature=0.4,
            max_tokens=3072,
        )

    @trace_agent("qa_gaming")
    def probe_ue58(self) -> dict[str, Any]:
        """Phase 21 — probe UE5.8 / PIE tools for gameplay QA."""
        from skills.skill_ue58 import probe_for_agent

        return probe_for_agent(self.AGENT_NAME)

    @trace_agent("qa_gaming")
    def list_recent_builds(self, limit: int = 5) -> dict[str, Any]:
        """Phase 21 — real build registry snapshot for test planning."""
        try:
            from database.supabase_client import get_supabase

            db = get_supabase()
            builds = db.select(
                "gaming_builds",
                order_by="created_at",
                ascending=False,
                limit=max(1, min(limit, 20)),
            )
            return {"ok": True, "builds": builds or [], "count": len(builds or [])}
        except Exception as exc:
            return {"ok": False, "builds": [], "error": str(exc)[:300]}
