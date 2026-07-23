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

import json
import logging
from collections.abc import Callable

from crewai import Agent, Crew, LLM, Task
from crewai.tools import tool

from skills.skill_coding_agent import execute_coding_task
from config.agent_operating_spec import crew_backstory
from skills.skill_langfuse import trace_agent
from skills.skill_nwiro import UE5_NOT_CONNECTED, nwiro_call, nwiro_is_available
from skills.skill_retry_loop import retry_with_learning

logger = logging.getLogger(__name__)

_telegram_notify: Callable[[str], None] | None = None


def execute_ue5_task_with_retry(
    agent_name: str,
    prompt: str,
    task_id: str | None = None,
    telegram_notify_fn: Callable[[str], None] | None = None,
) -> str:
    """Run a Nwiro prompt with intelligent retry on UE5 failures."""

    if not nwiro_is_available():
        return UE5_NOT_CONNECTED

    def _attempt(learning_context: str) -> str:
        if not nwiro_is_available():
            raise ConnectionError(UE5_NOT_CONNECTED)

        enriched_prompt = prompt
        if learning_context:
            enriched_prompt = (
                f"{prompt}\n\n"
                f"Note: Previous attempts failed. {learning_context}"
            )

        result = nwiro_call("ai_agent_prompt", {"prompt": enriched_prompt})

        if result and any(
            kw in result.lower() for kw in ("error", "failed", "cannot", "invalid")
        ):
            raise RuntimeError(f"Nwiro a retourné une erreur : {result[:300]}")

        return result

    retry_result = retry_with_learning(
        agent_name="dev_gaming",
        task_fn=_attempt,
        task_id=task_id,
        task_context=f"Prompt Nwiro : {prompt[:200]}",
        max_attempts=3,
        telegram_notify_fn=telegram_notify_fn,
    )

    if retry_result["success"]:
        return retry_result["result"]
    return "[ERREUR] Échec après 3 tentatives — escaladé au COO"


def _build_llm() -> LLM:
    from agents.base import build_crewai_llm

    return build_crewai_llm("dev_gaming", temperature=0.3)


@tool("nwiro_execute")
def nwiro_execute_tool(request_json: str) -> str:
    """
    Exécute une commande directement dans UE5 via le serveur MCP Nwiro (localhost:5353).
    Input JSON : {"tool": "blueprint_create_actor", "params": {...}}
    """
    try:
        if not nwiro_is_available():
            return UE5_NOT_CONNECTED

        data = json.loads(request_json)
        tool_name = data["tool"]
        params = data.get("params", {})

        def _attempt(learning_context: str) -> str:
            if not nwiro_is_available():
                raise ConnectionError(UE5_NOT_CONNECTED)
            result = nwiro_call(tool_name, params)
            if result and any(
                kw in str(result).lower() for kw in ("error", "failed", "cannot", "invalid")
            ):
                hint = f"\n{learning_context}" if learning_context else ""
                raise RuntimeError(f"Nwiro [{tool_name}] erreur : {str(result)[:300]}{hint}")
            return str(result)

        retry_result = retry_with_learning(
            agent_name="dev_gaming",
            task_fn=_attempt,
            task_id=tool_name,
            task_context=f"Nwiro tool: {tool_name}, params: {json.dumps(params)[:200]}",
            max_attempts=3,
            telegram_notify_fn=_telegram_notify,
        )
        if retry_result["success"]:
            return f"[OK] Nwiro [{tool_name}] : {retry_result['result']}"
        return f"[ERREUR] Erreur Nwiro après 3 tentatives : {retry_result['error']}"
    except json.JSONDecodeError as e:
        return f"[ERREUR] JSON invalide : {e}"
    except Exception as e:
        return f"[ERREUR] Erreur Nwiro : {e}"


@tool("nwiro_prompt")
def nwiro_prompt_tool(prompt: str) -> str:
    """
    Envoie un prompt en langage naturel à l'AI Agent intégré dans Nwiro.
    Nwiro interprète le prompt et exécute les outils UE5 nécessaires automatiquement.
    """
    try:
        if not nwiro_is_available():
            return UE5_NOT_CONNECTED

        result = execute_ue5_task_with_retry(
            agent_name="DevGaming",
            prompt=prompt,
            telegram_notify_fn=_telegram_notify,
        )
        if result == UE5_NOT_CONNECTED or result.startswith("[ERREUR]"):
            return result
        return f"[OK] Nwiro AI : {result}"
    except Exception as e:
        return f"[ERREUR] Erreur : {e}"


@tool("ue5_blueprint_spec")
def ue5_spec_tool(request: str) -> str:
    """
    Génère une spec technique UE5 (Blueprint ou C++) depuis une demande en langage naturel.
    """
    return f"""Spec UE5 pour : {request}

**TYPE :** Blueprint / C++ (à préciser selon complexité)

**Règle de choix :**
- Blueprint : logique gameplay, UI, animations, prototypage
- C++ : systèmes core, performance critique, plugins, réutilisabilité

**Nodes/Classes principaux :**
[Liste des Nodes Blueprint ou Classes C++ à utiliser]

**Input :** [Ce que reçoit le système]
**Output :** [Ce que produit le système]

**Événements :** BeginPlay / Tick / Custom Events

**Connexion naia-embodied (si applicable) :**
- WebSocket URL : wss://[supabase-url]/realtime/v1/...
- Format message : JSON {{ "action": "...", "data": {{...}} }}

**Tests à faire :**
[Comment valider que ça marche en PIE (Play In Editor)]

Note : Pour la connexion UE5 ↔ naia-embodied, utiliser le plugin WebSocket natif UE5.
Référence : https://docs.unrealengine.com/5.0/en-US/API/Runtime/WebSockets/"""


@tool("search_ue5_docs")
def ue5_docs_tool(query: str) -> str:
    """
    Recherche dans la documentation UE5 et retourne les références pertinentes.
    """
    ue5_refs = {
        "websocket": "https://docs.unrealengine.com/5.0/en-US/API/Runtime/WebSockets/",
        "http": "https://docs.unrealengine.com/5.0/en-US/API/Runtime/HTTP/",
        "blueprint": "https://docs.unrealengine.com/5.0/en-US/blueprints-visual-scripting-in-unreal-engine/",
        "multiplayer": "https://docs.unrealengine.com/5.0/en-US/networking-and-multiplayer-in-unreal-engine/",
        "holographic": "https://docs.lookingglassfactory.com/developer-tools/holoplay-sdk-unreal",
        "gameinstance": "https://docs.unrealengine.com/5.0/en-US/API/Runtime/Engine/Engine/UGameInstance/",
        "dataasset": "https://docs.unrealengine.com/5.0/en-US/API/Runtime/Engine/Engine/UPrimaryDataAsset/",
    }

    query_lower = query.lower()
    for key, url in ue5_refs.items():
        if key in query_lower:
            return (
                f"Documentation UE5 — {key.title()} :\n{url}\n\n"
                "Pour des exemples Blueprint spécifiques, consulte : "
                "https://www.unrealengine.com/marketplace/en-US/free"
            )

    return (
        f"Pour '{query}' dans UE5 :\n"
        f"https://docs.unrealengine.com/5.0/en-US/search/#q={query.replace(' ', '+')}"
    )


@tool("gaming_coding_agent")
def gaming_code_tool(spec_json: str) -> str:
    """
    Lance le pipeline de codage pour un repo UE5/gaming.
    Input JSON : même format que skill_coding_agent.
    """
    try:
        spec = json.loads(spec_json)
        spec["description"] = (
            f"[UE5/Gaming] {spec['description']}\n\n"
            "IMPORTANT : Précise toujours Blueprint vs C++. "
            "Respecte les conventions UE5 (préfixes U/A/F/E)."
        )
        result = execute_coding_task(spec, telegram_notify_fn=_telegram_notify)
        if result["success"]:
            return f"[OK] PR Gaming créée : {result['pr_url']}"
        return f"[ERREUR] Échec : {result['error']}"
    except Exception as e:
        return f"[ERREUR] Erreur : {e}"


class DevGamingAgent:
    def __init__(self, telegram_notify_fn: Callable[[str], None] | None = None):
        global _telegram_notify
        _telegram_notify = telegram_notify_fn
        self.telegram_notify = telegram_notify_fn

        self.agent = Agent(
            role="Dev Gaming — UE5 Specialist & Tuteur",
            goal=(
                "Implémenter les features UE5 de Wyrdheim et Naïa World via Nwiro. "
                "Guider Emilie dans son apprentissage UE5 en langage naturel. "
                "Toujours préciser Blueprint vs C++. Pouvoir exécuter directement dans UE5 via Nwiro."
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
            max_iter=10,
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
