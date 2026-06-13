"""Data Analyst Agent — Axel Roux, Data Analyst BI ALNUA."""

from __future__ import annotations

from typing import Any

from agents.base import LLMClient, log_agent_action, parse_json_response
from database.supabase_client import SupabaseClient, get_supabase
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from skills.skill_langfuse import trace_agent


class DataAnalystAgent:
    AGENT_NAME = "analyst_data"

    SYSTEM_PROMPT = """Tu es Axel Roux, Data Analyst BI d'ALNUA.
Layla Hassan (Business Analyst) cadre les questions, toi tu trouves les réponses dans la data. Vous êtes le même pipeline.

Tes spécialités :
- SQL (PostgreSQL/Supabase) pour l'extraction et l'agrégation
- Pandas pour l'exploration et le nettoyage
- Visualisations Hub (Recharts, Chart.js) et dashboards BI
- Analyse statistique et détection d'anomalies
- Tracking produit (events, funnels, rétention)

Méthode de travail :
Avant toute analyse, tu valides que les données sont complètes et cohérentes. Tu signales les anomalies de collecte avant d'interpréter.
Chaque SQL que tu génères inclut un commentaire expliquant la logique principale. Un SQL incompréhensible est un bug.

Règles de format :
Réponds en JSON valide. Le champ "sql" inclut des commentaires inline expliquant la logique.

Relation à la qualité :
Un graphique vaut mieux qu'un rapport de 20 pages."""

    def __init__(self, db: SupabaseClient | None = None, llm: LLMClient | None = None) -> None:
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()

    @trace_agent("analyst_data")
    def sql_query(
        self,
        question: str,
        schema_context: str,
        db_type: str = "postgresql",
    ) -> dict[str, Any]:
        """Génère une requête SQL pour répondre à une question analytique."""
        prompt = inject_learning_context(
            f"""Génère une requête SQL pour répondre à cette question analytique.
Question : {question}
Schéma de base de données :
{schema_context}
Type de BDD : {db_type}

Réponds en JSON :
{{
  "question": "{question}",
  "sql": "SELECT ...",
  "explanation": "Ce que la requête fait en langage naturel",
  "expected_output": "Description des colonnes retournées",
  "performance_notes": "Index recommandés ou points d'attention perf",
  "alternatives": ["Variante ou sous-requête alternative si utile"]
}}""",
            self.AGENT_NAME, question,
        )
        raw = self.llm.complete(
            self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.2
        )
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "sql_query",
            input_summary=question[:100],
            output_summary=f"SQL généré — {result.get('explanation', '')[:80]}",
        )
        try:
            record_task_learning(self.AGENT_NAME, "sql_query", str(result)[:300], success=True)
        except Exception:
            pass
        return result

    @trace_agent("analyst_data")
    def funnel_analysis(
        self,
        funnel_name: str,
        steps: list[str],
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """Analyse un funnel de conversion et identifie les points de friction."""
        steps_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(steps))
        prompt = inject_learning_context(
            f"""Analyse ce funnel de conversion.
Funnel : {funnel_name}
Étapes :
{steps_text}

Données :
{data}

Réponds en JSON :
{{
  "funnel_name": "{funnel_name}",
  "overall_conversion_rate": 0.0,
  "steps_analysis": [
    {{
      "step": "string",
      "users": 0,
      "conversion_from_previous": 0.0,
      "drop_off": 0.0,
      "verdict": "ok|attention|critical"
    }}
  ],
  "biggest_drop_off": "Étape avec le plus grand drop",
  "root_causes": ["Hypothèse de friction 1"],
  "recommendations": ["Action à mener 1"],
  "ab_test_suggestion": "string or null"
}}""",
            self.AGENT_NAME, funnel_name,
        )
        raw = self.llm.complete(
            self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.3
        )
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "funnel_analysis",
            input_summary=funnel_name,
            output_summary=f"Conversion: {result.get('overall_conversion_rate', '?')}% | Drop: {result.get('biggest_drop_off', '?')}",
        )
        return result

    @trace_agent("analyst_data")
    def anomaly_report(
        self,
        metric: str,
        recent_values: list[float],
        baseline: float,
        period: str = "7 jours",
    ) -> dict[str, Any]:
        """Détecte et explique une anomalie dans une métrique."""
        prompt = inject_learning_context(
            f"""Analyse cette anomalie de métrique.
Métrique : {metric}
Période : {period}
Baseline (moyenne historique) : {baseline}
Valeurs récentes : {recent_values}

Réponds en JSON :
{{
  "metric": "{metric}",
  "anomaly_detected": true,
  "direction": "up|down|spike|drop",
  "deviation_pct": 0.0,
  "severity": "critical|high|medium|low",
  "possible_causes": ["Cause probable 1", "Cause probable 2"],
  "data_quality_issue": false,
  "recommended_actions": ["Action 1"],
  "follow_up_metrics": ["Métrique à vérifier en parallèle"]
}}""",
            self.AGENT_NAME, f"anomaly {metric}",
        )
        raw = self.llm.complete(
            self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.2
        )
        return parse_json_response(raw)

    @trace_agent("analyst_data")
    def dashboard_spec(
        self,
        dashboard_name: str,
        audience: str,
        kpis: list[str],
        data_sources: list[str],
    ) -> dict[str, Any]:
        """Génère les spécifications d'un dashboard BI."""
        prompt = inject_learning_context(
            f"""Conçois les spécifications d'un dashboard BI.
Nom : {dashboard_name}
Audience : {audience}
KPIs à afficher : {', '.join(kpis)}
Sources de données : {', '.join(data_sources)}

Réponds en JSON :
{{
  "dashboard_name": "{dashboard_name}",
  "audience": "{audience}",
  "refresh_rate": "realtime|hourly|daily|weekly",
  "layout": [
    {{
      "section": "string",
      "charts": [
        {{
          "title": "string",
          "chart_type": "bar|line|pie|table|number|heatmap|funnel",
          "metric": "string",
          "dimensions": ["string"],
          "filters": ["string"],
          "notes": "string"
        }}
      ]
    }}
  ],
  "alerts": [
    {{ "metric": "string", "condition": "string", "channel": "slack|email" }}
  ],
  "implementation_notes": "Outil recommandé (Metabase, Recharts, etc.) et points d'attention"
}}""",
            self.AGENT_NAME, dashboard_name,
        )
        raw = self.llm.complete(
            self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.4, max_tokens=4096
        )
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "dashboard_spec",
            input_summary=f"{dashboard_name} | {audience}",
            output_summary=f"{sum(len(s.get('charts', [])) for s in result.get('layout', []))} graphiques",
        )
        return result
