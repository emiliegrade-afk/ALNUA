"""COO CrewAI setup — LLM, tools, and lazy agent initialization."""
from __future__ import annotations

from crewai import Agent, LLM
from crewai.tools import tool

from agents.coo_composio_tools import (
    connect_app_oauth,
    create_calendar_event,
    search_knowledge_base,
    send_email_via_gmail,
)
from agents.coo_constants import COO_SYSTEM_PROMPT
from agents.tools.hub_tools import HUB_TOOLS
from config.llm_runtime import CREWAI_MAX_ITER_COO
from skills.skill_composio import get_composio_tools
from skills.skill_gh_issues import create_github_issue, get_open_issues
from skills.skill_supabase import fetch_project_summary


class COOCrewMixin:
    """Requires project helpers, delegates, briefing, and ``self.verbose``."""

    def _ensure_crew(self) -> Agent:
        """Initialise CrewAI uniquement pour handle_instruction (pas le briefing)."""
        if self._crew_agent is None:
            self._llm = self._build_llm()
            self._tools = self._build_tools()
            self._crew_agent = self._build_crew_agent()
        return self._crew_agent

    def _build_llm(self) -> LLM:
        from agents.base import build_crewai_llm

        return build_crewai_llm("coo", temperature=0.3)

    def _build_crew_agent(self) -> Agent:
        assert self._tools is not None and self._llm is not None
        return Agent(
            role="COO — Directeur des Opérations",
            goal=(
                "Coordonner les projets ALNUA, répondre aux demandes d'Emilie avec des données "
                "réelles, déléguer au bon agent."
            ),
            backstory=(
                "Tu diriges ALNUA. Tu as accès aux projets, tickets, GitHub et coûts. "
                "Tu agis, tu ne demandes pas de clarifications inutiles.\n\n"
                + COO_SYSTEM_PROMPT
            ),
            tools=self._tools,
            llm=self._llm,
            verbose=self.verbose,
            allow_delegation=False,
            max_iter=CREWAI_MAX_ITER_COO,
        )

    def _build_tools(self) -> list:
        """Construit les outils CrewAI avec accès à l'instance COO."""
        coo = self

        @tool("get_project_context")
        def get_project_context(project_name: str) -> str:
            """Retourne l'état actuel d'un projet ALNUA depuis Supabase."""
            try:
                return coo._format_project_context(project_name)
            except Exception as exc:
                return f"Erreur lecture contexte : {exc}"

        @tool("get_open_tickets")
        def get_open_tickets(project_name: str) -> str:
            """Liste les tickets ouverts d'un projet."""
            try:
                tickets = coo._fetch_open_tickets(project_name)
                if not tickets:
                    return f"Aucun ticket ouvert pour {project_name}."
                lines = [
                    f"- [{t['priority']}] {t['title']} ({t['type']}) — id={t['id']}"
                    for t in tickets[:15]
                ]
                return "\n".join(lines)
            except Exception as exc:
                return f"Erreur tickets : {exc}"

        @tool("create_task_log")
        def create_task_log(
            agent: str,
            action: str,
            input_summary: str,
            output_summary: str,
            project_name: str = "",
        ) -> str:
            """Enregistre une action dans la table agent_logs Supabase."""
            try:
                project_id = None
                if project_name:
                    project = coo._find_project(project_name)
                    if project:
                        project_id = project["id"]
                row = coo.create_task_log(
                    agent, action, input_summary, output_summary, project_id
                )
                return f"Log créé : {row['id']}"
            except Exception as exc:
                return f"Erreur log : {exc}"

        @tool("get_daily_briefing")
        def get_daily_briefing_tool() -> str:
            """Résumé quotidien de tous les projets ALNUA."""
            try:
                briefing = coo.get_daily_briefing()
                return briefing["summary"]
            except Exception as exc:
                return f"Erreur briefing : {exc}"

        @tool("delegate_pm_agent")
        def delegate_pm_agent(project_name: str, instruction: str = "") -> str:
            """Délègue roadmap/tickets au pm_agent (exécute via API Hub)."""
            return coo._delegate_pm(project_name, instruction)

        @tool("delegate_qa_agent")
        def delegate_qa_agent(project_name: str) -> str:
            """Délègue l'analyse des feedbacks au qa_agent."""
            return coo._delegate_qa(project_name)

        @tool("delegate_content_agent")
        def delegate_content_agent(project_name: str) -> str:
            """Délègue la génération de posts au content_agent."""
            return coo._delegate_content(project_name)

        @tool("delegate_brainstorm_agent")
        def delegate_brainstorm_agent(project_name: str, topic: str) -> str:
            """Délègue une session d'idéation au brainstorm_agent."""
            return coo._delegate_brainstorm(project_name, topic)

        @tool("delegate_spec_agent")
        def delegate_spec_agent(ticket_id: str) -> str:
            """Délègue la génération d'un prompt Cursor au spec_agent."""
            return coo._delegate_spec(ticket_id)

        return [
            *HUB_TOOLS,
            *get_composio_tools(agent_name="coo_agent", user_id="alnua_coo"),
            get_open_issues,
            create_github_issue,
            fetch_project_summary,
            get_project_context,
            get_open_tickets,
            create_task_log,
            get_daily_briefing_tool,
            delegate_pm_agent,
            delegate_qa_agent,
            delegate_content_agent,
            delegate_brainstorm_agent,
            delegate_spec_agent,
            connect_app_oauth,
            send_email_via_gmail,
            create_calendar_event,
            search_knowledge_base,
        ]
