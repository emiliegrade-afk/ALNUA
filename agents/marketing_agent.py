"""
agents/marketing_agent.py

Agent CrewAI — Marketing/Community (Support Transversal)

Projets couverts : tous (Wyrdheim, Naïa App, Eve Journey's)
Responsabilités :
- SEO audits hebdomadaires (Lighthouse, Core Web Vitals)
- Gestion communauté Discord Wyrdheim
- Contenu réseaux sociaux (Gaming + App)
- Support utilisateurs Naïa App et Eve Journey's
- Veille concurrentielle mensuelle

Tools (max 5) : seo_analyzer, discord_manage, social_post, browser_use, support_tracker
"""

from __future__ import annotations

import json
import logging
import os
from collections.abc import Callable

from crewai import Agent, Crew, LLM, Task
from crewai.tools import tool

from skills.skill_browser_use import browse_url, search_web
from skills.skill_composio import get_composio_tools
from skills.skill_discord_wyrdheim import (
    DISCORD_NOT_CONFIGURED,
    discord_is_configured,
    get_recent_messages,
    post_to_discord,
)
from skills.skill_langfuse import trace_agent
from skills.skill_seo_audit import run_seo_audit

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


@tool("seo_audit")
def seo_audit_tool(url: str) -> str:
    """
    Lance un audit SEO sur une URL (Lighthouse + analyse basique).
    Input : URL complète (ex: https://wyrdheim.com)
    """
    try:
        return run_seo_audit(url)
    except Exception as e:
        return f"[ERREUR] Erreur audit SEO : {e}"


@tool("web_search")
def web_search_tool(query: str) -> str:
    """
    Recherche web pour veille concurrentielle et tendances.
    """
    try:
        results = search_web(query, limit=5)
        return "\n\n".join(
            [f"**{r['title']}**\n{r['url']}\n{r['snippet']}" for r in results]
        )
    except Exception as e:
        return f"[ERREUR] Erreur recherche : {e}"


@tool("browse_page")
def browse_tool(url: str) -> str:
    """
    Navigue sur une page web et extrait son contenu textuel.
    """
    try:
        return browse_url(url)[:2000]
    except Exception as e:
        return f"[ERREUR] Erreur navigation : {e}"


@tool("discord_community")
def discord_community_tool(action_json: str) -> str:
    """
    Gère la communauté Discord Wyrdheim.
    Input JSON : action (post|read|stats|announce), channel, content, pin.
    """
    try:
        if not discord_is_configured():
            return DISCORD_NOT_CONFIGURED

        data = json.loads(action_json)
        action = data.get("action", "read")

        if action == "post":
            result = post_to_discord(data["channel"], data["content"], data.get("embed", False))
            if not result.get("success"):
                return f"Discord indisponible : {result.get('error', 'erreur inconnue')}"
            return f"[OK] Posté dans #{data['channel']}"

        if action == "read":
            messages = get_recent_messages(data.get("channel", "général"), limit=20)
            return "\n".join([f"[{m['author']}] {m['content']}" for m in messages])

        if action == "stats":
            return "Stats Discord Wyrdheim : [À implémenter via Discord API]"

        return f"Action Discord '{action}' non reconnue."
    except Exception as e:
        return f"[ERREUR] Erreur Discord : {e}"


@tool("create_content")
def content_creator_tool(brief_json: str) -> str:
    """
    Génère du contenu marketing/community (posts, annonces, changelogs).
    Input JSON : type, project, topic, tone, length.
    """
    try:
        brief = json.loads(brief_json)
        project = brief.get("project", "wyrdheim")
        topic = brief.get("topic", "")
        tone = brief.get("tone", "épique")
        content_type = brief.get("type", "discord")

        tone_desc = (
            "dramatique, immersif, mythologique"
            if tone == "épique"
            else "clair, direct, informatif"
        )

        return f"""Contenu {content_type} pour {project} — Ton {tone}

**Sujet :** {topic}

[Génère ici un contenu {brief.get('length', 'moyen')} adapté au format {content_type}]

Pour Discord : utilise le formatage Markdown Discord (**gras**, *italique*, `code`, > citation)
Pour Twitter : max 280 chars, hashtags pertinents (#Wyrdheim #MMORPG #IndieGame)
Pour changelog : format version, date, sections Added/Changed/Fixed

Adapte le ton : {tone} = {tone_desc}"""
    except Exception as e:
        return f"[ERREUR] Erreur génération contenu : {e}"


class MarketingAgent:
    def __init__(self, telegram_notify_fn: Callable[[str], None] | None = None):
        composio_tools = get_composio_tools(
            agent_name="marketing_agent", user_id="alnua_marketing"
        )
        self.agent = Agent(
            role="Marketing & Community Manager",
            goal=(
                "Développer la visibilité d'ALNUA et engager les communautés. "
                "SEO optimal sur tous les produits. "
                "Communauté Wyrdheim active et positive sur Discord."
            ),
            backstory=(
                "Tu es le Marketing Director d'ALNUA, expert en growth marketing indie game et app. "
                "Tu maîtrises le SEO technique (Core Web Vitals, structured data), "
                "la gestion de communauté Discord, et le content marketing. "
                "Tu t'inspires des meilleures pratiques des studios indie (No Man's Sky, Hades, Hollow Knight). "
                "Tu analyses la concurrence et identifies les opportunités de différenciation. "
                "Tu adaptes le ton : épique pour Wyrdheim, bienveillant/scientifique pour Naïa, futuriste pour Eve."
            ),
            tools=[
                seo_audit_tool,
                web_search_tool,
                browse_tool,
                discord_community_tool,
                content_creator_tool,
                *composio_tools,
            ],
            llm=_build_llm(),
            max_iter=8,
            verbose=True,
        )

    @trace_agent("marketing_agent")
    def handle_instruction(self, instruction: str) -> str:
        task = Task(
            description=instruction,
            agent=self.agent,
            expected_output="Contenu créé, audit SEO, post Discord, ou rapport de veille.",
        )
        crew = Crew(agents=[self.agent], tasks=[task])
        return str(crew.kickoff())
