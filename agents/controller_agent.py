"""Controller Agent — Rémi Chassagne, Contrôleur de Gestion ALNUA."""

from __future__ import annotations

from typing import Any

from agents.base import LLMClient, log_agent_action, parse_json_response
from database.supabase_client import SupabaseClient, get_supabase
from skills.skill_agent_learning import inject_learning_context
from skills.skill_langfuse import trace_agent


class ControllerAgent:
    AGENT_NAME = "controller"

    SYSTEM_PROMPT = """Tu es Rémi Chassagne, Contrôleur de Gestion d'ALNUA.
Jules Bernard (Comptabilité) enregistre les faits. Toi tu projettes, analyses et recommandes. Vous êtes complémentaires, pas redondants.

Tes spécialités :
- Budget prévisionnel par projet et par équipe
- Suivi des coûts LLM (OpenRouter en priorité — poste variable le plus impactant d'ALNUA)
- Analyse P&L mensuelle et trimestrielle
- Forecasting de revenus et de dépenses
- Tableaux de bord financiers et KPIs business
- Recommandations d'optimisation des coûts

Méthode de travail :
Rigoureux, pragmatique, orienté données. Tes chiffres sont à 2 décimales.
Tes projections incluent toujours une fourchette basse/haute, jamais un chiffre sec.
Tu dis non avec des données, jamais avec des opinions.

Règles de format :
Réponds en JSON valide. Montants à 2 décimales. Projections avec range low/high.

Relation à la qualité :
On ne peut pas contrôler ce qu'on ne mesure pas."""

    def __init__(self, db: SupabaseClient | None = None, llm: LLMClient | None = None) -> None:
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()

    @trace_agent("controller")
    def analyze_costs(
        self,
        period: str,
        costs_data: dict[str, Any],
        budget: dict[str, float] | None = None,
    ) -> dict[str, Any]:
        """Analyse les coûts sur une période et compare au budget."""
        prompt = inject_learning_context(
            f"""Analyse ces données de coûts pour la période : {period}

Données de coûts :
{costs_data}

Budget prévu : {budget or 'Non défini'}

Réponds en JSON :
{{
  "period": "{period}",
  "total_costs": 0.00,
  "by_category": {{}},
  "vs_budget": {{
    "status": "under|on_track|over",
    "variance_pct": 0.0,
    "comment": "string"
  }},
  "top_cost_drivers": ["string"],
  "alerts": [{{ "severity": "critical|warning|info", "message": "string" }}],
  "recommendations": ["string"]
}}""",
            self.AGENT_NAME, f"cost analysis {period}",
        )
        raw = self.llm.complete(
            self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.2
        )
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "analyze_costs",
            input_summary=f"Période: {period}",
            output_summary=f"Total: {result.get('total_costs', '?')} | Status: {result.get('vs_budget', {}).get('status', '?')}",
        )
        return result

    @trace_agent("controller")
    def build_forecast(
        self,
        project: str,
        horizon_months: int,
        assumptions: str,
        historical_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Construit un forecast financier sur N mois."""
        prompt = inject_learning_context(
            f"""Construis un forecast financier pour {project} sur {horizon_months} mois.

Hypothèses de base : {assumptions}
Données historiques : {historical_data or 'Démarrage / pas encore de données'}

Réponds en JSON :
{{
  "project": "{project}",
  "horizon_months": {horizon_months},
  "monthly_forecast": [
    {{ "month": "2026-07", "revenue": 0.0, "costs": 0.0, "net": 0.0, "notes": "string" }}
  ],
  "break_even_month": "string or null",
  "total_investment_needed": 0.0,
  "confidence": "low|medium|high",
  "key_assumptions": ["string"],
  "risks": ["string"]
}}""",
            self.AGENT_NAME, f"forecast {project}",
        )
        raw = self.llm.complete(
            self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.3, max_tokens=4096
        )
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "build_forecast",
            input_summary=f"{project} | {horizon_months} mois",
            output_summary=f"Break-even: {result.get('break_even_month', '?')} | Confiance: {result.get('confidence', '?')}",
        )
        return result

    @trace_agent("controller")
    def llm_cost_alert(self, daily_spend: float, monthly_budget: float) -> dict[str, Any]:
        """Évalue le spend LLM du jour et génère une alerte si nécessaire."""
        days_in_month = 30
        projected_monthly = daily_spend * days_in_month
        pct = (projected_monthly / monthly_budget * 100) if monthly_budget else 0

        status = "ok"
        if pct > 100:
            status = "critical"
        elif pct > 80:
            status = "warning"
        elif pct > 60:
            status = "watch"

        prompt = inject_learning_context(
            f"""Analyse ce spend LLM quotidien et génère un rapport.
Dépense aujourd'hui : ${daily_spend:.4f}
Projection mensuelle : ${projected_monthly:.2f}
Budget mensuel LLM : ${monthly_budget:.2f}
Pourcentage du budget : {pct:.1f}%

Réponds en JSON :
{{
  "status": "{status}",
  "daily_spend": {daily_spend},
  "projected_monthly": {projected_monthly:.2f},
  "budget": {monthly_budget},
  "pct_used": {pct:.1f},
  "message": "Analyse et recommandation concise",
  "action": "string or null"
}}""",
            self.AGENT_NAME, "llm cost alert",
        )
        raw = self.llm.complete(
            self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.1
        )
        return parse_json_response(raw)

    @trace_agent("controller")
    def monthly_report(self, month: str, all_data: dict[str, Any]) -> dict[str, Any]:
        """Génère le rapport financier mensuel complet."""
        prompt = inject_learning_context(
            f"""Génère le rapport financier mensuel d'ALNUA pour {month}.

Données du mois :
{all_data}

Réponds en JSON :
{{
  "month": "{month}",
  "executive_summary": "Résumé pour Aria (3-4 phrases max)",
  "revenue": {{ "total": 0.0, "by_project": {{}} }},
  "costs": {{ "total": 0.0, "by_category": {{}} }},
  "net": 0.0,
  "vs_previous_month": {{ "revenue_change_pct": 0.0, "costs_change_pct": 0.0 }},
  "highlights": ["Point positif du mois"],
  "concerns": ["Point d'attention"],
  "next_month_outlook": "string"
}}""",
            self.AGENT_NAME, f"monthly report {month}",
        )
        raw = self.llm.complete(
            self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.2, max_tokens=3000
        )
        return parse_json_response(raw)
