"""Plan executor — COO plan generation and parsing."""

from __future__ import annotations

import logging

from config.agent_personas import persona_prompt_intro
from services.agent_pipeline_registry import format_plan_executor_catalog
from services.dev_ownership import OWNERSHIP_RULES
from services.plan_executor_models import ExecutionPlan, ExecutionStep

logger = logging.getLogger(__name__)

_COO_PLAN_SYSTEM = f"""{persona_prompt_intro("coo", role="COO")}. Tu décomposes des objectifs en plans d'action précis.
Chaque étape du plan est assignée à UN agent ALNUA spécifique avec ses paramètres exacts.
Les dépendances reflètent le flux de données réel (step B utilise le résultat de step A).
NUAWAY = app voyage nomade (spots, cartes, communauté) — pas de tickets VPN/crypto/R&D sans lien.
Réponds en JSON valide uniquement."""

_AVAILABLE_AGENTS = format_plan_executor_catalog()


def _ownership_hint() -> str:
    lines = ["Ownership dev (à respecter STRICTEMENT dès qu'une étape touche du code) :"]
    for rule_cls in OWNERSHIP_RULES:
        rule = rule_cls()
        lines.append(f"- {rule.agent_id} ({rule.label}) : {rule.description}")
    lines.append(
        "- dev_integrator (Intégrateur) : merge les worktrees des autres devs vers la branche "
        "commune, ne code jamais de feature lui-même"
    )
    lines.append("- qa : review obligatoire avant tout merge d'intégration")
    lines.append(
        "Ne JAMAIS assigner toutes les étapes de code au même agent_id par défaut : répartis "
        "chaque étape vers l'agent dont l'ownership correspond au fichier/stack réellement "
        "concerné, pour que l'équipe travaille en parallèle plutôt qu'un seul agent qui "
        "fait tout."
    )
    return "\n".join(lines)


_OWNERSHIP_HINT = _ownership_hint()


def parse_coo_plan(objective: str, context: str = "") -> ExecutionPlan:
    """Ask Aria (COO) for a JSON plan and parse it into ExecutionPlan."""
    try:
        from agents.base import LLMClient, parse_json_response

        llm = LLMClient()
        prompt = f"""OBJECTIF : {objective}
CONTEXTE : {context or 'Aucun contexte supplémentaire'}

{_AVAILABLE_AGENTS}

{_OWNERSHIP_HINT}

Génère un plan d'exécution JSON avec :
- title (string): titre court du plan
- steps (list): liste des étapes, chaque étape = {{
    "step_id": "1" | "2" | ...,
    "description": "Ce que cette étape accomplit",
    "agent_id": "agent_id exact de la liste ci-dessus",
    "method": "méthode exacte de l'agent",
    "kwargs": {{paramètres pour la méthode}},
    "depends_on": ["step_id_bloquant"] — vide [] si indépendant
  }}

Règles :
- Maximum 8 étapes
- Minimiser les dépendances (exécution parallèle quand possible)
- Les kwargs doivent être utilisables tels quels par l'agent
- Grouper les étapes indépendantes (même niveau de depends_on = parallèles)
- Une étape de code = un agent_id dev dont l'ownership correspond réellement au fichier/stack concerné
  (voir ownership dev ci-dessus) — jamais un seul agent dev par défaut pour tout le plan
- Ne pas créer de tickets PM sur NUAWAY pour des sujets R&D sans lien produit (ex: VPN russe)
- Recherche R&D pure → agent rnd_agent / analyst_business, pas de tickets sur les apps existantes"""

        raw = llm.complete(_COO_PLAN_SYSTEM, prompt, agent_id="coo", temperature=0.3)
        data = parse_json_response(raw)

        steps = []
        for s in data.get("steps", []):
            steps.append(
                ExecutionStep(
                    step_id=str(s.get("step_id", len(steps) + 1)),
                    description=s.get("description", ""),
                    agent_id=s.get("agent_id", ""),
                    method=s.get("method", ""),
                    kwargs=s.get("kwargs", {}),
                    depends_on=[str(d) for d in s.get("depends_on", [])],
                )
            )

        return ExecutionPlan(
            title=data.get("title", objective[:50]),
            steps=steps,
            context=context,
            objective=objective,
        )

    except Exception as e:
        logger.error(f"COO plan parse failed: {e}")
        return ExecutionPlan(
            title=objective[:50], steps=[], context=context, objective=objective
        )
