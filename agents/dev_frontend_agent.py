"""Dev Frontend Agent — Inès Moreau, développeuse Frontend Hub (Next.js / React) ALNUA."""

from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from agents.base import log_agent_action, parse_json_response, run_with_learning
from config.agent_operating_spec import get_system_prompt
from skills.skill_agent_learning import inject_learning_context
from skills.skill_langfuse import trace_agent


class DevFrontendAgent(AgentBase):
    AGENT_NAME = "dev_frontend"

    SYSTEM_PROMPT = get_system_prompt("dev_frontend")

    @trace_agent("dev_frontend")
    def implement_ui(
        self,
        feature: str,
        project: str = "Hub ALNUA",
        context: str = "",
        design_notes: str = "",
    ) -> str:
        """Génère le code d'implémentation frontend (composants React/Next.js) pour une feature."""
        prompt = inject_learning_context(
            f"""Implémente cette feature frontend complète.
Projet : {project}
Feature : {feature}
Contexte : {context or 'Voir ticket / spec associée'}
Notes design : {design_notes or 'Design system Hub standard (voir web/src/components/ui/)'}

Génère tous les fichiers nécessaires avec le format :
===SUMMARY===
...
===FILE:path/fichier.tsx===
...code...
===END===

Inclus : composant, états (loading, empty, error, edge), responsive, accessibilité (aria).""",
            self.AGENT_NAME, feature,
        )
        result = run_with_learning(
            self.AGENT_NAME, f"implement UI {feature}",
            self.llm.complete,
            self.SYSTEM_PROMPT, prompt,
            agent_id=self.AGENT_NAME, temperature=0.25, max_tokens=8192,
        )
        log_agent_action(
            self.db, self.AGENT_NAME, "implement_ui",
            input_summary=f"{project} | {feature}",
            output_summary=f"{result[:150]}...",
        )
        return result

    @trace_agent("dev_frontend")
    def fix_layout(self, issue: str, context: str = "", code_snippet: str = "") -> dict[str, Any]:
        """Diagnostique et corrige un problème de layout/UI."""
        prompt = inject_learning_context(
            f"""Diagnostique et corrige ce problème de layout/UI.
Problème : {issue}
Contexte : {context}
Code concerné :
```
{code_snippet[:2000]}
```

Réponds en JSON :
{{
  "diagnosis": "Cause probable en une phrase",
  "root_cause": "Explication détaillée (flexbox/grid/responsive/z-index/etc.)",
  "fix_code": "Code corrigé (snippet ou fichier complet)",
  "responsive_checked": ["mobile", "desktop"],
  "prevention": "Comment éviter ce bug à l'avenir"
}}""",
            self.AGENT_NAME, issue[:100],
        )
        raw = self._complete(prompt, temperature=0.2)
        return parse_json_response(raw)

    @trace_agent("dev_frontend")
    def review_component(self, code: str, context: str = "") -> dict[str, Any]:
        """Revue de code frontend : accessibilité, responsive, perf, cohérence design system."""
        prompt = inject_learning_context(
            f"""Effectue une revue de code frontend professionnelle.
Contexte : {context or 'Composant Hub ALNUA'}

```
{code[:4000]}
```

Réponds en JSON :
{{
  "score": 7,
  "issues": [
    {{ "severity": "critical|major|minor", "line": null, "description": "string", "fix": "string" }}
  ],
  "accessibility_flags": ["aria manquant, contraste, focus..."],
  "responsive_flags": ["breakpoints manquants..."],
  "positives": ["Ce qui est bien fait"],
  "suggestions": ["Amélioration recommandée"]
}}""",
            self.AGENT_NAME, "component review",
        )
        raw = self._complete(prompt, temperature=0.2)
        return parse_json_response(raw)

    def handle_instruction(self, instruction: str) -> str:
        """Point d'entrée générique : reçoit une instruction en langage naturel du COO / plan executor."""
        from skills.skill_agent_learning import get_learning_context, record_task_learning

        memory_block = get_learning_context(self.AGENT_NAME, instruction)
        prompt = f"{instruction}{memory_block}"
        result = run_with_learning(
            self.AGENT_NAME, instruction[:120],
            self.llm.complete,
            self.SYSTEM_PROMPT, prompt,
            agent_id=self.AGENT_NAME, temperature=0.3, max_tokens=8192,
        )
        try:
            record_task_learning(agent_id=self.AGENT_NAME, task=instruction, outcome=result)
        except Exception:
            pass
        log_agent_action(
            self.db, self.AGENT_NAME, "handle_instruction",
            input_summary=instruction[:200],
            output_summary=f"{result[:150]}...",
        )
        return result
