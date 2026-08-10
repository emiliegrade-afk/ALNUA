"""MVP plan generation for App Factory."""

from __future__ import annotations

import logging
import os

from agents.base import LLMClient, parse_json_response
from skills.skill_langfuse import trace_agent

from services.app_factory_models import FactoryTask, _FACTORY_STACK

logger = logging.getLogger(__name__)


def fallback_plan(name: str, brief: str, stack: _FACTORY_STACK) -> list[FactoryTask]:
    """Deterministic MVP when LLM unavailable (tests / dry-run)."""
    if stack == "expo":
        return [
            FactoryTask(
                title=f"{name} — scaffold Expo",
                description=(
                    f"Initialiser l'app Expo pour {name}.\n\nBrief:\n{brief[:500]}"
                ),
                files_to_create=["app.json", "App.tsx", "package.json", "tsconfig.json"],
                tests_to_pass=["npx expo export --platform web"],
                priority="P0",
            ),
            FactoryTask(
                title=f"{name} — écran d'accueil MVP",
                description="Écran principal avec navigation de base et thème ALNUA.",
                files_to_create=["src/screens/HomeScreen.tsx", "src/theme/colors.ts"],
                files_to_modify=["App.tsx"],
                tests_to_pass=["npx expo start --non-interactive"],
                priority="P1",
            ),
        ]
    return [
        FactoryTask(
            title=f"{name} — scaffold Next.js",
            description=(
                f"Initialiser le projet Next.js App Router pour {name}.\n\nBrief:\n{brief[:500]}"
            ),
            files_to_create=[
                "package.json",
                "next.config.mjs",
                "tsconfig.json",
                "src/app/layout.tsx",
                "src/app/page.tsx",
                "src/app/globals.css",
            ],
            tests_to_pass=["npm run build"],
            priority="P0",
        ),
        FactoryTask(
            title=f"{name} — page MVP + layout",
            description="Page d'accueil MVP alignée sur le brief, Tailwind + structure Hub.",
            files_to_create=["src/components/home-hero.tsx"],
            files_to_modify=["src/app/page.tsx", "src/app/layout.tsx"],
            tests_to_pass=["npm run lint", "npm run build"],
            priority="P1",
        ),
    ]


@trace_agent("spec_agent")
def generate_factory_plan(
    name: str,
    brief: str,
    stack: _FACTORY_STACK,
    *,
    dry_run: bool = False,
) -> list[FactoryTask]:
    """Léon + Sam lightweight — JSON task breakdown for MVP."""
    if dry_run or os.getenv("APP_FACTORY_DRY_RUN", "").lower() in ("1", "true", "yes"):
        return fallback_plan(name, brief, stack)

    stack_label = "Next.js 14 App Router" if stack == "nextjs" else "React Native Expo"
    system = """Tu es Léon (Spec) + Sam (PM) d'ALNUA.
Transforme un brief produit en plan MVP codable par dev_app.
Réponds UNIQUEMENT en JSON valide:
{
  "tasks": [
    {
      "title": "string",
      "description": "string (détaillé, actionnable)",
      "files_to_create": ["chemins/relatifs"],
      "files_to_modify": ["chemins/relatifs"],
      "tests_to_pass": ["commandes shell"],
      "priority": "P0|P1"
    }
  ]
}
Règles: 2 à 4 tâches max, la première = scaffold, chemins réalistes, pas de blabla."""
    prompt = (
        f"App: {name}\nStack: {stack_label}\n\nBrief:\n{brief}\n\n"
        "Génère le plan MVP (scaffold + features P0)."
    )
    llm = LLMClient()
    try:
        raw = llm.complete(system, prompt, agent_id="spec_agent", temperature=0.35)
        data = parse_json_response(raw)
        tasks_raw = data.get("tasks") if isinstance(data, dict) else None
        if not isinstance(tasks_raw, list) or not tasks_raw:
            raise ValueError("tasks missing")
        tasks = [FactoryTask.model_validate(t) for t in tasks_raw[:4]]
        return tasks
    except Exception as exc:
        logger.warning("generate_factory_plan LLM fallback: %s", exc)
        return fallback_plan(name, brief, stack)
