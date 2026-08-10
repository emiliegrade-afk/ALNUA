"""
agents/dev_gaming_agent.py

Agent CrewAI — Dev Gaming (Pôle Gaming)

Projets : Wyrdheim Online, Naïa World
Responsabilités :
- Blueprint et C++ UE5 pour Wyrdheim et Naïa World
- Connexion UE5 ↔ naia-embodied (WebSocket)
- HoloPlay SDK pour Looking Glass
- Outils modding pour la communauté Wyrdheim
- PRs automatiques sur repos UE5

Tools (max 5) : nwiro_execute, nwiro_prompt, ue5_blueprint_spec, search_ue5_docs, gaming_coding_agent
Règle : TOUJOURS préciser Blueprint vs C++ dans les réponses et specs.
"""

from __future__ import annotations

import logging
from collections.abc import Callable

from crewai import Agent, Crew, LLM, Task

from agents.dev_gaming_tools import (
    gaming_code_tool,
    nwiro_execute_tool,
    nwiro_prompt_tool,
    set_telegram_notify,
    ue5_docs_tool,
    ue5_spec_tool,
)
from config.llm_runtime import CREWAI_MAX_ITER_DEFAULT
from config.agent_operating_spec import crew_backstory
from skills.skill_langfuse import trace_agent

logger = logging.getLogger(__name__)


def _build_llm() -> LLM:
    from agents.base import build_crewai_llm

    return build_crewai_llm("dev_gaming", temperature=0.3)


class DevGamingAgent:
    def __init__(self, telegram_notify_fn: Callable[[str], None] | None = None):
        set_telegram_notify(telegram_notify_fn)
        self.telegram_notify = telegram_notify_fn

        self.agent = Agent(
            role="Dev Gaming — UE5 Specialist & Tuteur",
            goal=(
                "Implémenter les features UE5.8 de Wyrdheim/Naïa World. "
                "Agency PC : gaming_coding_agent (Claude Code sur UE_PROJECT_PATH). "
                "Éditeur : Nwiro legacy ou serveur UE5.8. Toujours Blueprint vs C++."
            ),
            backstory=crew_backstory("dev_gaming"),
            tools=[
                nwiro_execute_tool,
                nwiro_prompt_tool,
                ue5_spec_tool,
                ue5_docs_tool,
                gaming_code_tool,
            ],
            llm=_build_llm(),
            max_iter=CREWAI_MAX_ITER_DEFAULT,
            verbose=True,
        )

    @trace_agent("dev_gaming_agent")
    def handle_instruction(self, instruction: str) -> str:
        from skills.skill_agent_learning import get_learning_context, record_task_learning

        memory_block = get_learning_context("dev_gaming", instruction)
        task = Task(
            description=(
                f"{instruction}\n\n"
                "CONSIGNES :\n"
                "- Si c'est une demande d'explication/apprentissage : explique clairement, "
                "étape par étape, avec des exemples concrets liés à Wyrdheim/Naïa World. "
                "N'exécute pas dans UE5 sauf si demandé explicitement.\n"
                "- Si c'est une demande d'implémentation directe : utilise nwiro_prompt "
                "pour envoyer un prompt précis à Nwiro, ou nwiro_execute pour des outils spécifiques.\n"
                "- Toujours préciser Blueprint ou C++ et pourquoi.\n"
                "- Toujours vérifier que Nwiro est accessible avant d'exécuter."
                f"{memory_block}"
            ),
            agent=self.agent,
            expected_output=(
                "Explication pédagogique, spec UE5 détaillée, "
                "ou confirmation d'exécution dans UE5 avec résultat Nwiro."
            ),
        )
        crew = Crew(agents=[self.agent], tasks=[task])
        _result = str(crew.kickoff())
        try:
            record_task_learning(agent_id="dev_gaming", task=instruction, outcome=_result)
        except Exception:
            pass
        return _result
