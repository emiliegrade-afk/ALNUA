"""Industrial Design Agent — Elin Bergström, design produit ALNUA Robotique."""
from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt
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
        prompt = f"""Conçois l'identité produit pour {product_name} (Eve robot).
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
}}"""
        return self.run_json_task(
            action="design_form_factor",
            prompt=prompt,
            learning_key=product_name,
            input_summary=f"{product_name}",
            output_summary=lambda r: f"{len(r.get('materials_finish', []))} choix matière/finition",
            temperature=0.6,
            max_tokens=2048,
        )
