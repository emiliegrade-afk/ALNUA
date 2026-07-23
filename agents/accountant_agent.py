"""
accountant_agent.py — Agent comptable ALNUA pour dossiers R&D.

Wraps rule-based estimates + optional LLM commentary.
"""

from __future__ import annotations

from agents.agent_base import AgentBase

import logging
from typing import Any

from agents.base import log_agent_action, parse_json_response
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from services.rnd_finance_estimate import (
    estimate_rnd_project,
    finance_json_to_markdown,
)
from config.agent_operating_spec import get_system_prompt
from skills.skill_langfuse import trace_agent

logger = logging.getLogger(__name__)


class AccountantAgent(AgentBase):
    AGENT_NAME = "accounting"
    SYSTEM_PROMPT = get_system_prompt("accounting")


    @trace_agent("accountant_agent")
    def estimate_for_dossier(
        self,
        dossier: dict[str, Any],
        idea: dict[str, Any] | None = None,
        *,
        constraint: str | None = None,
        add_commentary: bool = False,
    ) -> dict[str, Any]:
        """Return finance_json + markdown business case."""
        idea = idea or {}
        section_text = _dossier_section_text(dossier)
        finance = estimate_rnd_project(
            title=dossier.get("title", ""),
            description=idea.get("description") or dossier.get("tagline") or "",
            domain=dossier.get("domain"),
            effort=idea.get("effort"),
            db=self.db,
            constraint=constraint,
            section_text=section_text,
        )

        md = finance_json_to_markdown(finance)

        if add_commentary and self.llm._settings.openrouter_api_key.strip():
            try:
                from skills.skill_agent_learning import inject_learning_context, record_task_learning

                rev = finance.get("revenue_hypothesis") or {}
                pricing = rev.get("pricing_model") or {}
                commentary_prompt = inject_learning_context(
                    f"Dossier: {dossier.get('title')}\n"
                    f"Domaine: {dossier.get('domain')}\n"
                    f"CAPEX: {finance['capex_eur']} EUR\n"
                    f"OPEX: {finance['opex_monthly_eur']} EUR/mois\n"
                    f"Pricing: {pricing.get('price_range_eur')} ARPU={rev.get('blended_arpu_eur')} EUR\n"
                    f"Abonnés M12: {(rev.get('paying_subscribers') or {}).get('m12')}\n"
                    f"MRR M12: {rev.get('m12_monthly_run_rate_eur')} EUR/mois\n"
                    f"Verdict: {finance['verdict_finance']}\n"
                    f"Contrainte: {constraint or 'aucune'}\n\n"
                    "Ajoute un paragraphe d'analyse et une recommandation.",
                    "accounting",
                    dossier.get("title", "estimate"),
                )
                commentary = self._complete(commentary_prompt, temperature=0.3, max_tokens=400)
                md += f"\n\n### Analyse comptable\n\n{commentary.strip()}"
                finance["accountant_commentary"] = commentary.strip()
            except Exception as exc:
                logger.warning("accountant_agent: LLM commentary failed: %s", exc)

        log_agent_action(
            self.db,
            self.AGENT_NAME,
            "estimate_dossier",
            input_summary=dossier.get("title", "")[:80],
            output_summary=f"verdict={finance.get('verdict_finance')} capex={finance.get('capex_eur')}",
            status="success",
        )
        try:
            from skills.skill_agent_learning import record_task_learning

            outcome = (
                f"verdict={finance.get('verdict_finance')} "
                f"capex={finance.get('capex_eur')}"
            )
            if finance.get("accountant_commentary"):
                outcome += f" | {finance['accountant_commentary'][:200]}"
            record_task_learning(
                agent_id="accounting",
                task=f"estimate {dossier.get('title', '')}",
                outcome=outcome,
                success=True,
            )
        except Exception:
            pass
        return {"finance_json": finance, "business_case_md": md}

    @trace_agent("accountant_agent")
    def financial_advice(
        self,
        month: str,
        financial_summary: dict[str, Any],
        question: str,
    ) -> dict[str, Any]:
        """Conseil comptable sur la période (transactions, trésorerie, charges)."""
        prompt = inject_learning_context(
            f"""Période : {month}

Résumé financier :
{financial_summary}

Question d'Emilie :
{question}

Réponds en JSON :
{{
  "synthese": "2-3 phrases sur la situation",
  "alertes": ["point d'attention"],
  "recommandations": ["action concrète"],
  "prochaine_etape": "une seule action prioritaire"
}}""",
            self.AGENT_NAME,
            month,
        )
        raw = self._complete(prompt, temperature=0.3, max_tokens=800)
        result = parse_json_response(raw)
        log_agent_action(
            self.db,
            self.AGENT_NAME,
            "financial_advice",
            input_summary=f"{month} | {question[:80]}",
            output_summary=str(result.get("synthese", ""))[:100],
        )
        try:
            record_task_learning(
                self.AGENT_NAME,
                f"conseil {month}",
                str(result)[:300],
                success=True,
            )
        except Exception:
            pass
        return result


def _dossier_section_text(dossier: dict[str, Any]) -> str:
    """Concatenate market/mvp/solution sections for pricing extraction."""
    parts: list[str] = []
    for sec in dossier.get("sections") or []:
        key = sec.get("section_key") if isinstance(sec, dict) else getattr(sec, "section_key", None)
        if key in ("market", "mvp", "solution", "business_case"):
            content = sec.get("content_md") if isinstance(sec, dict) else getattr(sec, "content_md", "")
            if content:
                parts.append(str(content))
    return "\n\n".join(parts)
