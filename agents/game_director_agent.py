"""
agents/game_director_agent.py

Agent CrewAI — Game Director (Pôle Gaming)

Projets gérés : Wyrdheim Online, Naïa World
Responsabilités :
- Vision créative et cohérence des univers
- Base de données lore (personnages, factions, histoire, mythologie)
- Design règles de jeu, équilibrage, économie MMORPG
- Quêtes, événements émergents, level design narratif
- Posts communauté Discord Wyrdheim

Tools (max 5) : lore_database, quest_generator, economy_simulator, discord_post, research_web
Règle : Ne touche jamais au code UE5. Produit des specs que Dev Gaming implémente.
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable

from crewai import Agent, Crew, LLM, Task
from crewai.tools import tool

from skills.skill_discord_wyrdheim import get_recent_messages, post_to_discord
from skills.skill_langfuse import trace_agent
from skills.skill_lore_database import add_lore_entry, search_lore

logger = logging.getLogger(__name__)


def _build_llm() -> LLM:
    from config.settings import get_settings

    settings = get_settings()
    model = os.getenv("AGENT_MODEL", "openrouter/minimax/minimax-m1")
    if not model.startswith("openrouter/"):
        model = f"openrouter/{model}"
    return LLM(
        model=model,
        base_url=settings.openrouter_base_url,
        api_key=settings.openrouter_api_key,
        temperature=0.3,
    )


@tool("lore_search")
def lore_search_tool(query: str) -> str:
    """
    Recherche dans la base de données lore Wyrdheim/Naïa World.
    Input : requête en langage naturel (ex: "histoire des Seigneurs Wyrd", "pouvoirs de Naïa")
    Output : entrées lore correspondantes formatées
    """
    results = search_lore(query)
    if not results:
        return f"Aucune entrée lore trouvée pour '{query}'. Tu peux en créer une avec lore_add."
    return "\n\n".join(
        [
            f"**{r['title']}** ({r['category']})\n{r['content'][:500]}..."
            for r in results
        ]
    )


@tool("lore_add")
def lore_add_tool(entry_json: str) -> str:
    """
    Ajoute une entrée dans la base de données lore.
    Input JSON :
    {
      "title": "Les Seigneurs Wyrd",
      "category": "factions",
      "project": "wyrdheim",
      "content": "Description complète...",
      "tags": ["faction", "antagoniste"]
    }
    """
    try:
        entry = json.loads(entry_json)
        result = add_lore_entry(entry)
        return f"✅ Entrée lore créée : '{entry['title']}' (ID: {result.get('id', '?')})"
    except Exception as e:
        return f"❌ Erreur : {e}"


@tool("quest_generator")
def quest_generator_tool(context_json: str) -> str:
    """
    Génère une quête complète (titre, objectifs, récompenses, lore) depuis un contexte.
    Input JSON avec type, zone, level_range, lore_theme, constraints.
    """
    try:
        ctx = json.loads(context_json)
        return f"""Quête générée pour {ctx.get('zone', 'zone inconnue')} :

**Titre :** [À générer selon le thème '{ctx.get('lore_theme')}']
**Type :** {ctx.get('type', 'secondaire')}
**Level :** {ctx.get('level_range', '1-10')}
**Objectifs :**
1. Objectif principal
2. Objectif secondaire (optionnel)
**Récompenses :** XP, Or, Item rare lié au lore
**Narration :** Contexte lore de la quête
**PNJ impliqués :** Noms et motivations
**Contraintes :** {ctx.get('constraints', 'Aucune')}

Note : Développe chaque section en cohérence avec le lore existant via lore_search."""
    except Exception as e:
        return f"❌ Erreur : {e}"


@tool("discord_wyrdheim_post")
def discord_post_tool(message_json: str) -> str:
    """
    Poste un message dans le Discord Wyrdheim.
    Input JSON : channel, content, embed (optionnel).
    """
    try:
        data = json.loads(message_json)
        post_to_discord(data["channel"], data["content"], data.get("embed", False))
        return f"✅ Posté dans #{data['channel']}"
    except Exception as e:
        return f"❌ Erreur Discord : {e}"


@tool("discord_read_community")
def discord_read_tool(channel: str = "général") -> str:
    """
    Lit les derniers messages d'un channel Discord Wyrdheim.
    Utile pour suivre les retours communautaires.
    """
    try:
        messages = get_recent_messages(channel, limit=20)
        if not messages:
            return f"Aucun message récent dans #{channel}"
        return "\n".join([f"[{m['author']}] {m['content']}" for m in messages])
    except Exception as e:
        return f"❌ Erreur lecture Discord : {e}"


class GameDirectorAgent:
    def __init__(self, telegram_notify_fn: Callable[[str], None] | None = None):
        self.telegram_notify = telegram_notify_fn

        self.agent = Agent(
            role="Game Director",
            goal=(
                "Créer et maintenir des univers de jeu cohérents, immersifs et profonds. "
                "Wyrdheim Online et Naïa World doivent avoir un lore riche, des mécaniques équilibrées "
                "et une communauté engagée sur Discord."
            ),
            backstory=(
                "Tu es le Game Director créatif d'ALNUA, spécialiste des MMORPGs et des mondes ouverts. "
                "Tu t'inspires de l'Elder Scrolls, Dark Souls, et Final Fantasy XIV pour le world-building. "
                "Tu maîtrises la mythologie nordique (Wyrdheim) et les thèmes ésotériques (Naïa World). "
                "Tu produis des specs précises que Dev Gaming peut implémenter directement. "
                "Tu ne codes jamais — tu design et tu écris."
            ),
            tools=[
                lore_search_tool,
                lore_add_tool,
                quest_generator_tool,
                discord_post_tool,
                discord_read_tool,
            ],
            llm=_build_llm(),
            max_iter=8,
            verbose=True,
        )

    @trace_agent("game_director_agent")
    def handle_instruction(self, instruction: str) -> str:
        task = Task(
            description=instruction,
            agent=self.agent,
            expected_output=(
                "Contenu lore, spec de quête, design document, ou post Discord selon la demande."
            ),
        )
        crew = Crew(agents=[self.agent], tasks=[task])
        return str(crew.kickoff())
