"""PM Agent — project management: roadmap, sprint planning, ticket triage."""

from __future__ import annotations

import logging
from typing import Any

from crewai import Agent, Crew, LLM, Process, Task

from agents.base import LLMClient, log_agent_action, parse_json_response
from agents.tools.hub_tools import PM_TOOLS
from database.supabase_client import SupabaseClient, get_supabase
from skills.skill_composio import get_composio_tools
from skills.skill_gh_issues import get_open_issues, label_issue
from skills.skill_langfuse import trace_agent

logger = logging.getLogger(__name__)

PM_SYSTEM_PROMPT = """Tu es le Project Manager virtuel d'ALNUA.
Tu gères roadmap, tickets et priorisation.

Règles :
- Utilise TOUJOURS les outils Hub (Lister les projets, Créer un ticket, Créer un item roadmap)
  pour toute action concrète — ne décris jamais une action sans l'exécuter via l'outil.
- Appelle « Lister les projets » pour obtenir le project_id UUID avant de créer un ticket ou un item roadmap.
- Réponds en français, court et actionnable (3-5 lignes max)."""


class PMAgent:
    AGENT_NAME = "pm_agent"

    SYSTEM_PROMPT = """Tu es le Project Manager virtuel d'ALNUA.
Tu priorises la roadmap, proposes des sprints et tries les tickets.
Réponds UNIQUEMENT en JSON valide avec cette structure :
{
  "sprint_name": "string",
  "priorities": [{"roadmap_id": "uuid or null", "title": "string", "reason": "string"}],
  "ticket_actions": [{"ticket_id": "uuid", "new_status": "open|in_progress|done|wont_fix", "reason": "string"}],
  "summary": "string"
}"""

    def __init__(
        self,
        db: SupabaseClient | None = None,
        llm: LLMClient | None = None,
        verbose: bool = False,
    ) -> None:
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()
        self.verbose = verbose
        self._crew_llm: LLM | None = None
        self._crew_agent: Agent | None = None

    def _build_crew_llm(self) -> LLM:
        from config.settings import get_settings

        settings = get_settings()
        model = settings.default_llm_model
        if not model.startswith("openrouter/"):
            model = f"openrouter/{model}"
        return LLM(
            model=model,
            base_url=settings.openrouter_base_url,
            api_key=settings.openrouter_api_key,
            temperature=0.3,
        )

    def _ensure_crew_agent(self) -> Agent:
        if self._crew_agent is None:
            self._crew_llm = self._build_crew_llm()
            composio_tools = get_composio_tools(
                agent_name="pm_agent", user_id="alnua_pm"
            )
            self._crew_agent = Agent(
                role="PM ALNUA",
                goal="Gérer roadmap et tickets via l'API Hub ALNUA",
                backstory=PM_SYSTEM_PROMPT,
                tools=[*PM_TOOLS, *composio_tools, get_open_issues, label_issue],
                llm=self._crew_llm,
                verbose=self.verbose,
                allow_delegation=False,
                max_iter=10,
            )
        return self._crew_agent

    @trace_agent("pm_agent")
    def handle_instruction(self, instruction: str, project_id: str | None = None) -> str:
        """Exécute une instruction PM via CrewAI + outils API Hub."""
        instruction = instruction.strip()
        if not instruction:
            return "Instruction vide."

        project_hint = ""
        if project_id:
            rows = self.db.select("projects", filters={"id": project_id})
            if rows:
                project_hint = (
                    f"\nProjet cible : {rows[0]['name']} (project_id={project_id})"
                )

        crew_agent = self._ensure_crew_agent()
        task = Task(
            description=(
                f"Instruction : {instruction}{project_hint}\n\n"
                "Exécute les actions via les outils Hub. "
                "Confirme ce qui a été créé ou modifié."
            ),
            expected_output="Résumé en 3-5 lignes des actions réellement exécutées via l'API.",
            agent=crew_agent,
        )

        try:
            crew = Crew(
                agents=[crew_agent],
                tasks=[task],
                process=Process.sequential,
                verbose=self.verbose,
            )
            result = crew.kickoff()
            summary = result.raw if hasattr(result, "raw") else str(result)
            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "handle_instruction",
                input_summary=instruction[:500],
                output_summary=summary[:500],
                status="success",
                project_id=project_id,
            )
            return summary
        except Exception as exc:
            logger.exception("PM handle_instruction failed")
            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "handle_instruction",
                input_summary=instruction[:500],
                output_summary=str(exc),
                status="error",
                project_id=project_id,
            )
            raise

    def triage_project(self, project_id: str) -> dict[str, Any]:
        tickets = self.db.select("tickets", filters={"project_id": project_id})
        roadmap = self.db.select(
            "roadmap",
            filters={"project_id": project_id},
            order_by="priority",
            ascending=False,
        )
        project = self.db.select("projects", filters={"id": project_id})
        if not project:
            raise ValueError(f"Project {project_id} not found")

        user_prompt = f"""Projet : {project[0]['name']} ({project[0]['branch']})
Tickets ouverts : {tickets}
Roadmap : {roadmap}

Propose un triage et plan de sprint."""

        try:
            raw = self.llm.complete(self.SYSTEM_PROMPT, user_prompt, temperature=0.3)
            result = parse_json_response(raw)

            for action in result.get("ticket_actions", []):
                ticket_id = action.get("ticket_id")
                new_status = action.get("new_status")
                if ticket_id and new_status:
                    self.db.update("tickets", ticket_id, {"status": new_status})

            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "triage_project",
                input_summary=f"project={project_id}, tickets={len(tickets)}",
                output_summary=result.get("summary", "")[:500],
                status="success",
                project_id=project_id,
            )
            return result
        except Exception as exc:
            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "triage_project",
                input_summary=f"project={project_id}",
                output_summary=str(exc),
                status="error",
                project_id=project_id,
            )
            raise

    def add_roadmap_item(
        self,
        project_id: str,
        title: str,
        description: str = "",
        phase: str = "",
        priority: str = "medium",
        status: str = "planned",
    ) -> dict[str, Any]:
        row = self.db.insert(
            "roadmap",
            {
                "project_id": project_id,
                "title": title,
                "description": description,
                "phase": phase,
                "priority": priority,
                "status": status,
            },
        )
        log_agent_action(
            self.db,
            self.AGENT_NAME,
            "add_roadmap_item",
            input_summary=title,
            output_summary=row["id"],
            project_id=project_id,
        )
        return row

    def update_roadmap_status(self, roadmap_id: str, status: str) -> dict[str, Any]:
        return self.db.update("roadmap", roadmap_id, {"status": status})
