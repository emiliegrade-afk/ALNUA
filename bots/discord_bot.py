"""Discord Bot — ALNUA Hub command interface on Discord."""

from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from agents.brainstorm_agent import BrainstormAgent
from agents.content_agent import ContentAgent
from agents.coo_agent import COOAgent
from agents.pm_agent import PMAgent
from agents.qa_agent import QAAgent
from agents.spec_agent import SpecAgent
from bots.base import log_bot_action
from config.settings import get_settings
from database.supabase_client import get_supabase

logger = logging.getLogger(__name__)

BOT_NAME = "discord_bot"


class DiscordBot:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.db = get_supabase()
        intents = discord.Intents.default()
        intents.message_content = True
        self.bot = commands.Bot(command_prefix="!alnua ", intents=intents)
        self._register_commands()

    def _register_commands(self) -> None:
        @self.bot.event
        async def on_ready() -> None:
            logger.info("Discord bot connected as %s", self.bot.user)
            log_bot_action(self.db, BOT_NAME, "on_ready", "", str(self.bot.user))

        @self.bot.command(name="briefing")
        async def briefing(ctx: commands.Context) -> None:
            await ctx.send("Génération du briefing COO en cours…")
            agent = COOAgent(self.db)
            result = await asyncio.to_thread(agent.run_daily_briefing)
            if len(result) > 1900:
                for chunk in [result[i : i + 1900] for i in range(0, len(result), 1900)]:
                    await ctx.send(chunk)
            else:
                await ctx.send(result)

        @self.bot.command(name="triage")
        async def triage(ctx: commands.Context, project_id: str) -> None:
            await ctx.send(f"Triage du projet `{project_id}`…")
            agent = PMAgent(self.db)
            result = await asyncio.to_thread(agent.triage_project, project_id)
            await ctx.send(f"✅ {result.get('summary', 'Triage terminé.')}")

        @self.bot.command(name="qa")
        async def qa(ctx: commands.Context, project_id: str) -> None:
            await ctx.send("Analyse QA des feedbacks…")
            agent = QAAgent(self.db)
            result = await asyncio.to_thread(agent.analyze_feedback_batch, project_id)
            await ctx.send(result.get("summary", "Analyse terminée."))

        @self.bot.command(name="content")
        async def content(ctx: commands.Context, project_id: str) -> None:
            await ctx.send("Génération de contenu depuis les dev logs…")
            agent = ContentAgent(self.db)
            posts = await asyncio.to_thread(agent.generate_from_dev_logs, project_id)
            await ctx.send(f"✅ {len(posts)} post(s) créé(s) en attente d'approbation.")

        @self.bot.command(name="brainstorm")
        async def brainstorm_cmd(ctx: commands.Context, project_id: str, *, topic: str) -> None:
            await ctx.send(f"Brainstorm sur « {topic} »…")
            agent = BrainstormAgent(self.db)
            result = await asyncio.to_thread(agent.brainstorm, project_id, topic)
            ideas = result.get("ideas", [])
            lines = [f"**{i['title']}** ({i.get('effort', '?')} effort / {i.get('impact', '?')} impact)" for i in ideas[:5]]
            await ctx.send("\n".join(lines) or "Aucune idée générée.")

        @self.bot.command(name="spec")
        async def spec(ctx: commands.Context, ticket_id: str) -> None:
            await ctx.send(f"Génération du prompt Cursor pour `{ticket_id}`…")
            agent = SpecAgent(self.db)
            ticket = await asyncio.to_thread(agent.generate_cursor_prompt, ticket_id)
            prompt = ticket.get("cursor_prompt", "")
            preview = prompt[:500] + ("…" if len(prompt) > 500 else "")
            await ctx.send(f"✅ Prompt généré ({len(prompt)} chars)\n```\n{preview}\n```")

        @self.bot.command(name="projects")
        async def projects(ctx: commands.Context) -> None:
            rows = self.db.select("projects", order_by="branch")
            lines = [f"• **{p['name']}** (`{p['id']}`) — {p['branch']} / {p['status']}" for p in rows]
            await ctx.send("\n".join(lines) or "Aucun projet.")

    def run(self) -> None:
        if not self.settings.discord_token:
            raise RuntimeError("DISCORD_TOKEN is not configured")
        self.bot.run(self.settings.discord_token)


def run_discord_bot() -> None:
    logging.basicConfig(level=logging.INFO)
    DiscordBot().run()


if __name__ == "__main__":
    run_discord_bot()
