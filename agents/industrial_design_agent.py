"""Industrial Design Agent — Elin Bergström, design produit ALNUA Robotique."""

from __future__ import annotations

from agents.agent_base import AgentBase

from typing import Any

from agents.base import log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from skills.skill_langfuse import trace_agent


class IndustrialDesignAgent(AgentBase):
    AGENT_NAME = "industrial_design"

    SYSTEM_PROMPT = get_system_prompt("industrial_design")

    @trace_agent("industrial_design")
    def design_form_factor(
        self,
        product_name: str,
        constraints: str = "",
        brand_notes: str = "",
    ) -> dict[str, Any]:
        """Conçoit l'identité produit (forme, finitions, ergonomie) d'Eve ou d'un composant visible."""
        prompt = inject_learning_context(
            f"""Conçois l'identité produit pour {product_name} (Eve robot).
Contraintes mécaniques/électroniques existantes : {constraints or 'À vérifier avec Ravi Chandrasekaran'}
Notes de marque ALNUA : {brand_notes or 'Cohérence avec identité visuelle Max Delacroix'}

Réponds en JSON :
{{
  "product": "{product_name}",
  "form_direction": "Description de la direction de forme choisie",
  "materials_finish": [{{ "part": "string", "material": "string", "finish": "string" }}],
  "ergonomics_notes": "Points d'interaction physique à soigner",
  "prototyping_plan": "Méthode de prototypage rapide recommandée",
  "handoff_notes": "Notes pour Ravi Chandrasekaran (faisabilité mécanique)"
}}""",
            self.AGENT_NAME, product_name,
        )
        raw = self._complete(prompt, temperature=0.6, max_tokens=2048)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "design_form_factor",
            input_summary=f"{product_name}",
            output_summary=f"{len(result.get('materials_finish', []))} choix matière/finition",
        )
        try:
            record_task_learning(self.AGENT_NAME, "design_form_factor", str(result)[:400], success=True)
        except Exception:
            pass
        return result
