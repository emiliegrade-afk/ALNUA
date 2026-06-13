"""Dev Backend Agent — Hao Chen, développeur Backend & API ALNUA."""

from __future__ import annotations

from typing import Any

from agents.base import LLMClient, log_agent_action, parse_json_response, run_with_learning
from database.supabase_client import SupabaseClient, get_supabase
from skills.skill_agent_learning import inject_learning_context
from skills.skill_langfuse import trace_agent


class DevBackendAgent:
    AGENT_NAME = "dev_backend"

    SYSTEM_PROMPT = """Tu es Hao Chen, développeur Backend & API d'ALNUA.
Théo Laurent (Dev App) construit le front, toi les fondations. Vos livraisons se mesurent en features opérationnelles end-to-end.

Tes spécialités :
- APIs REST et WebSocket (FastAPI, Node.js, Express)
- Bases de données (Supabase / PostgreSQL, optimisation de requêtes)
- Authentification et sécurité (JWT, OAuth, RLS Supabase)
- Infrastructure et déploiement (Docker, CI/CD, Railway, Fly.io)
- Intégrations tierces (webhooks, SDKs)

Méthode de travail :
Méthodique, silencieux, orienté fondations. Standards ALNUA : typage strict, docstrings, gestion d'erreurs explicite, pas de print() en production.
Chaque endpoint que tu conçois doit être documenté, versionné (/api/v1/) et prévoir la pagination si la liste peut dépasser 100 items.

Règles de format :
Pour le code, utilise TOUJOURS le format :
===SUMMARY===
<résumé de ce que tu as fait>
===FILE:path/to/file.ext===
<contenu complet du fichier>
===END===
Pour les specs et analyses, réponds en JSON valide.

Relation à la qualité :
Le front, c'est la vitrine. Moi je suis la fondation."""

    def __init__(self, db: SupabaseClient | None = None, llm: LLMClient | None = None) -> None:
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()

    @trace_agent("dev_backend")
    def design_api(
        self,
        feature: str,
        project: str,
        constraints: str = "",
    ) -> dict[str, Any]:
        """Conçoit la structure d'une API pour une feature donnée."""
        prompt = inject_learning_context(
            f"""Conçois l'architecture API pour cette feature.
Projet : {project}
Feature : {feature}
Contraintes : {constraints or 'Stack ALNUA standard (FastAPI + Supabase)'}

Réponds en JSON :
{{
  "endpoints": [
    {{
      "method": "GET|POST|PUT|DELETE|PATCH",
      "path": "/api/v1/...",
      "description": "string",
      "auth_required": true,
      "request_body": {{}} ,
      "response_example": {{}}
    }}
  ],
  "database_changes": ["Migration SQL ou table à créer"],
  "estimated_complexity": "low|medium|high",
  "dependencies": ["libs ou services externes"]
}}""",
            self.AGENT_NAME, feature,
        )
        raw = self.llm.complete(
            self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.3
        )
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "design_api",
            input_summary=f"{project} | {feature}",
            output_summary=f"{len(result.get('endpoints', []))} endpoints",
        )
        return result

    @trace_agent("dev_backend")
    def implement_feature(
        self,
        feature: str,
        project: str,
        api_spec: str = "",
        tech_stack: str = "FastAPI + Supabase",
    ) -> str:
        """Génère le code d'implémentation backend pour une feature."""
        prompt = inject_learning_context(
            f"""Implémente cette feature backend complète.
Projet : {project}
Feature : {feature}
Stack : {tech_stack}
Spec API : {api_spec or 'À définir selon les besoins'}

Génère tous les fichiers nécessaires avec le format :
===SUMMARY===
...
===FILE:path/fichier.py===
...code...
===END===

Inclus : routes, modèles, validation, gestion d'erreurs, tests basiques.""",
            self.AGENT_NAME, feature,
        )
        result = run_with_learning(
            self.AGENT_NAME, f"implement {feature}",
            self.llm.complete,
            self.SYSTEM_PROMPT, prompt,
            agent_id=self.AGENT_NAME, temperature=0.2, max_tokens=8192,
        )
        log_agent_action(
            self.db, self.AGENT_NAME, "implement_feature",
            input_summary=f"{project} | {feature}",
            output_summary=f"{result[:150]}...",
        )
        return result

    @trace_agent("dev_backend")
    def review_code(self, code: str, context: str = "") -> dict[str, Any]:
        """Effectue une revue de code backend."""
        prompt = inject_learning_context(
            f"""Effectue une revue de code backend professionnelle.
Contexte : {context or 'Code ALNUA'}

```
{code[:4000]}
```

Réponds en JSON :
{{
  "score": 7,
  "issues": [
    {{ "severity": "critical|major|minor", "line": null, "description": "string", "fix": "string" }}
  ],
  "positives": ["Ce qui est bien fait"],
  "suggestions": ["Amélioration recommandée"],
  "security_flags": ["Problèmes de sécurité éventuels"]
}}""",
            self.AGENT_NAME, "code review",
        )
        raw = self.llm.complete(
            self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.2
        )
        return parse_json_response(raw)

    @trace_agent("dev_backend")
    def debug(self, error: str, context: str, code_snippet: str = "") -> dict[str, Any]:
        """Analyse et propose des solutions pour un bug backend."""
        prompt = inject_learning_context(
            f"""Analyse ce bug backend et propose des solutions.
Erreur : {error}
Contexte : {context}
Code concerné :
```
{code_snippet[:2000]}
```

Réponds en JSON :
{{
  "diagnosis": "Cause probable en une phrase",
  "root_cause": "Explication détaillée",
  "fixes": [
    {{ "approach": "string", "code": "string", "confidence": "high|medium|low" }}
  ],
  "prevention": "Comment éviter ce bug à l'avenir"
}}""",
            self.AGENT_NAME, error[:100],
        )
        raw = self.llm.complete(
            self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.2
        )
        return parse_json_response(raw)
