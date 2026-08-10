"""Product Engineering Spec — Pydantic models and LLM prompts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field

from config.agent_personas import persona_prompt_intro

ENGINEERING_SPEC_OUTLINE = """
## 10. Product Engineering Spec (PRD technique)

Structure OBLIGATOIRE :
### 10.1 Contexte & objectifs
### 10.2 Écrans / parcours utilisateur
### 10.3 User stories (format : En tant que… je veux… afin de…)
### 10.4 Contrat API (méthode, route, auth, payload, réponse)
### 10.5 Schéma Supabase (tables, colonnes clés, RLS)
### 10.6 Tests E2E / critères d'acceptation
### 10.7 Task breakdown JSON (liste ordonnée de tâches agent-ready)
"""

_SPEC_INTRO = persona_prompt_intro("spec", role="Spec Rédacteur")
_PM_INTRO = persona_prompt_intro("pm", role="PM")

ENGINEERING_SPEC_SYSTEM = _SPEC_INTRO + """.
Tu produis la section 10 « Product Engineering Spec » d'un dossier CEO validé.

Stack par défaut pour apps voyage / NUAWAY : React Native Expo + Supabase + Mapbox.
Stack Hub ALNUA : Python FastAPI + Next.js + Supabase.

Réponds UNIQUEMENT en JSON valide :
{
  "engineering_spec_md": "markdown complet section 10 (### 10.1 à 10.6)",
  "stack": "react_native_expo|nextjs|python_fastapi|godot",
  "screens": [{"id": "screen_id", "name": "...", "route": "...", "description": "..."}],
  "user_stories": [{"id": "US-001", "story": "En tant que...", "acceptance": ["..."]}],
  "api_contract": [{"method": "GET", "route": "/api/...", "auth": "...", "description": "..."}],
  "supabase_tables": [{"name": "...", "columns": ["..."], "rls": "..."}],
  "e2e_tests": [{"id": "E2E-001", "scenario": "...", "steps": ["..."]}],
  "task_breakdown": [
    {
      "id": "T-001",
      "title": "Court titre actionnable",
      "description": "Ce qui doit être implémenté",
      "stack": "react_native_expo",
      "files_create": ["path/to/new.tsx"],
      "files_modify": ["path/to/existing.ts"],
      "tests": ["tests/test_x.py"],
      "priority": "P0|P1|P2",
      "sprint": 1,
      "depends_on": [],
      "agent_id": "dev_app|dev_frontend|dev_backend|dev_gaming|embedded_dev"
    }
  ]
}

Règles :
- 40 à 80 tâches pour un MVP ambitieux (NUAWAY-like), 15-25 pour un petit scope.
- Chaque tâche = 1 PR / 1 issue agent (2-4h dev agent).
- Titres commençant par un verbe d'action.
- depends_on = ids de tâches du même breakdown.
- agent_id DOIT refléter les fichiers concernés, pas un choix par défaut : mobile/Expo → dev_app,
  Hub web (web/, .tsx/.jsx) → dev_frontend, API/services/Python/SQL → dev_backend, jeux Godot → dev_gaming,
  firmware/robotique → embedded_dev. Ne jamais assigner toutes les tâches au même agent_id : répartis
  selon le stack réel de chaque tâche pour que l'équipe travaille en parallèle.
- Ne pas inventer de features hors scope dossier."""

TASK_BREAKDOWN_PM_SYSTEM = _PM_INTRO + """.
Tu affines le task_breakdown JSON d'une engineering spec pour publication GitHub.

Réponds UNIQUEMENT en JSON :
{
  "task_breakdown": [ ... même structure, champs id/title/description/stack/files_create/files_modify/tests/priority/sprint/depends_on/agent_id ... ],
  "sprint_plan": [{"sprint": 1, "goal": "...", "task_ids": ["T-001"]}],
  "notes": "arbitrages PM"
}

Règles :
- Garder l'ordre logique (setup → auth → core features → polish).
- P0 = bloquant MVP, P1 = important, P2 = nice-to-have.
- Ne pas fusionner plusieurs features en une seule tâche."""


class EngineeringTask(BaseModel):
    id: str
    title: str
    description: str = ""
    stack: str = "react_native_expo"
    files_create: list[str] = Field(default_factory=list)
    files_modify: list[str] = Field(default_factory=list)
    tests: list[str] = Field(default_factory=list)
    priority: str = "P1"
    sprint: int = 1
    depends_on: list[str] = Field(default_factory=list)
    agent_id: str = ""


class EngineeringSpecResult(BaseModel):
    engineering_spec_md: str
    stack: str = "react_native_expo"
    screens: list[dict[str, Any]] = Field(default_factory=list)
    user_stories: list[dict[str, Any]] = Field(default_factory=list)
    api_contract: list[dict[str, Any]] = Field(default_factory=list)
    supabase_tables: list[dict[str, Any]] = Field(default_factory=list)
    e2e_tests: list[dict[str, Any]] = Field(default_factory=list)
    task_breakdown: list[EngineeringTask] = Field(default_factory=list)
    sprint_plan: list[dict[str, Any]] = Field(default_factory=list)
    qa_verdict: str | None = None
    generated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()
