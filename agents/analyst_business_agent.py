"""Business Analyst Agent — Layla Hassan, Business Analyst ALNUA."""

from __future__ import annotations

from agents.agent_base import AgentBase

from typing import Any

from agents.base import log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from skills.skill_langfuse import trace_agent


class BusinessAnalystAgent(AgentBase):
    AGENT_NAME = "analyst_business"

    SYSTEM_PROMPT = get_system_prompt("analyst_business")


    @trace_agent("analyst_business")
    def market_analysis(
        self,
        product: str,
        market: str,
        competitors: list[str] | None = None,
    ) -> dict[str, Any]:
        """Analyse le marché cible et la position concurrentielle d'un produit."""
        prompt = inject_learning_context(
            f"""Effectue une analyse de marché pour ce produit.
Produit : {product}
Marché cible : {market}
Concurrents identifiés : {', '.join(competitors) if competitors else 'À identifier'}

Réponds en JSON :
{{
  "market_size": "Estimation du marché (TAM/SAM/SOM)",
  "target_users": "Description du persona cible",
  "pain_points": ["Problème 1", "Problème 2"],
  "competitors": [
    {{
      "name": "string",
      "strengths": ["string"],
      "weaknesses": ["string"],
      "pricing": "string",
      "market_position": "string"
    }}
  ],
  "opportunities": ["Opportunité 1"],
  "threats": ["Menace 1"],
  "differentiation": "Comment ALNUA se démarque",
  "recommended_positioning": "Recommandation de positionnement",
  "confidence": "low|medium|high"
}}""",
            self.AGENT_NAME, f"market analysis {product}",
        )
        raw = self._complete(prompt, temperature=0.5, max_tokens=4096)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "market_analysis",
            input_summary=f"{product} | {market}",
            output_summary=f"{len(result.get('competitors', []))} concurrents | {len(result.get('opportunities', []))} opportunités",
        )
        try:
            record_task_learning(self.AGENT_NAME, "market_analysis", str(result)[:400], success=True)
        except Exception:
            pass
        return result

    @trace_agent("analyst_business")
    def define_kpis(
        self,
        project: str,
        stage: str,
        business_goal: str,
    ) -> dict[str, Any]:
        """Définit les KPIs pertinents pour un projet à un stade donné."""
        prompt = inject_learning_context(
            f"""Définis les KPIs pour ce projet.
Projet : {project}
Stade : {stage} (pre-launch|beta|launch|growth|mature)
Objectif business principal : {business_goal}

Réponds en JSON :
{{
  "north_star_metric": {{ "name": "string", "definition": "string", "target": "string" }},
  "primary_kpis": [
    {{ "name": "string", "definition": "string", "target": "string", "frequency": "daily|weekly|monthly", "tool": "string" }}
  ],
  "secondary_kpis": [...],
  "anti_metrics": ["Métriques à éviter ou qui donnent une fausse impression de succès"],
  "review_cadence": "weekly|biweekly|monthly"
}}""",
            self.AGENT_NAME, f"kpis {project}",
        )
        raw = self._complete(prompt, temperature=0.3)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "define_kpis",
            input_summary=f"{project} | {stage}",
            output_summary=f"North star: {result.get('north_star_metric', {}).get('name', '?')}",
        )
        return result

    @trace_agent("analyst_business")
    def user_research(
        self,
        product: str,
        research_question: str,
        user_segment: str = "",
    ) -> dict[str, Any]:
        """Génère un plan de user research et analyse les insights."""
        prompt = inject_learning_context(
            f"""Conçois un plan de user research et anticipe les insights.
Produit : {product}
Question de recherche : {research_question}
Segment utilisateur cible : {user_segment or 'Utilisateurs généraux'}

Réponds en JSON :
{{
  "research_question": "{research_question}",
  "methodology": "Interview|Survey|Usability test|Analytics review",
  "participant_profile": "Description du profil idéal",
  "sample_size": 10,
  "questions": ["Question d'interview 1", "Question d'interview 2"],
  "hypotheses": ["Hypothèse à valider 1"],
  "expected_insights": ["Insight probable 1"],
  "success_criteria": "Comment sait-on que la recherche est concluante"
}}""",
            self.AGENT_NAME, research_question,
        )
        raw = self._complete(prompt, temperature=0.5)
        return parse_json_response(raw)

    @trace_agent("analyst_business")
    def strategic_brief(
        self,
        topic: str,
        context: str,
        decision_needed: str,
    ) -> dict[str, Any]:
        """Rédige un brief stratégique pour aider à une prise de décision."""
        prompt = inject_learning_context(
            f"""Rédige un brief stratégique pour Aria (COO) d'ALNUA.
Sujet : {topic}
Contexte : {context}
Décision à prendre : {decision_needed}

Réponds en JSON :
{{
  "title": "string",
  "executive_summary": "2-3 phrases max pour Aria",
  "situation": "Analyse de la situation actuelle",
  "options": [
    {{ "option": "string", "pros": ["string"], "cons": ["string"], "effort": "low|medium|high", "impact": "low|medium|high" }}
  ],
  "recommendation": "Option recommandée et pourquoi",
  "next_steps": ["Action concrète 1"],
  "deadline_sensitivity": "urgent|normal|flexible"
}}""",
            self.AGENT_NAME, topic,
        )
        raw = self._complete(prompt, temperature=0.4, max_tokens=3000)
        return parse_json_response(raw)
