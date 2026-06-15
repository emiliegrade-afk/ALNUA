"""QA Agent — analyzes feedback and crash reports, creates tickets."""

from __future__ import annotations

from typing import Any

from crewai import Agent, LLM

from agents.base import LLMClient, log_agent_action, parse_json_response
from agents.tools.hub_tools import QA_TOOLS
from config.agent_personas import persona_prompt_intro
from database.supabase_client import SupabaseClient, get_supabase
from skills.skill_langfuse import trace_agent


_QA_INTRO = persona_prompt_intro("qa", role="QA")

class QAAgent:
    AGENT_NAME = "qa_agent"

    SYSTEM_PROMPT = _QA_INTRO + """. Analyse les retours utilisateurs et rapports
pour identifier bugs, crashes et améliorations.
Réponds UNIQUEMENT en JSON valide :
{
  "tickets": [
    {
      "type": "bug|feature|improvement|crash",
      "priority": "critical|high|medium|low",
      "title": "string",
      "description": "string"
    }
  ],
  "summary": "string"
}
Ne crée pas de doublons évidents. Sois précis et actionnable."""

    def __init__(self, db: SupabaseClient | None = None, llm: LLMClient | None = None) -> None:
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()
        self._crew_llm: LLM | None = None
        self._crew_agent: Agent | None = None

    def _build_crew_llm(self) -> LLM:
        from agents.base import build_crewai_llm

        return build_crewai_llm("qa", temperature=0.2)

    def _ensure_crew_agent(self) -> Agent:
        if self._crew_agent is None:
            self._crew_llm = self._build_crew_llm()
            self._crew_agent = Agent(
                role="QA ALNUA",
                goal="Analyser les retours et gérer les tickets via l'API Hub",
                backstory=self.SYSTEM_PROMPT,
                tools=QA_TOOLS,
                llm=self._crew_llm,
                allow_delegation=False,
                max_iter=10,
            )
        return self._crew_agent

    @trace_agent("qa_agent")
    def analyze_feedback_batch(self, project_id: str, limit: int = 20) -> dict[str, Any]:
        feedback_items = self.db.select(
            "feedback",
            filters={"project_id": project_id, "status": "new"},
            limit=limit,
        )
        if not feedback_items:
            return {"tickets": [], "summary": "Aucun feedback nouveau à analyser."}

        existing_tickets = self.db.select(
            "tickets",
            filters={"project_id": project_id, "status": "open"},
            limit=50,
        )

        user_prompt = f"""Feedback à analyser :
{feedback_items}

Tickets ouverts existants (éviter doublons) :
{existing_tickets}"""

        from skills.skill_agent_learning import inject_learning_context, record_task_learning

        user_prompt = inject_learning_context(
            user_prompt, "qa", f"analyze feedback project {project_id}"
        )

        try:
            raw = self.llm.complete(
                self.SYSTEM_PROMPT, user_prompt, agent_id="qa", temperature=0.2
            )
            result = parse_json_response(raw)
            created: list[dict[str, Any]] = []

            for ticket_data in result.get("tickets", []):
                row = self.db.insert(
                    "tickets",
                    {
                        "project_id": project_id,
                        "type": ticket_data["type"],
                        "priority": ticket_data["priority"],
                        "title": ticket_data["title"],
                        "description": ticket_data.get("description", ""),
                        "source": "qa_agent",
                        "status": "open",
                    },
                )
                created.append(row)

            for fb in feedback_items:
                self.db.update("feedback", fb["id"], {"status": "processed"})

            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "analyze_feedback_batch",
                input_summary=f"{len(feedback_items)} feedback items",
                output_summary=f"{len(created)} tickets créés",
                status="success",
                project_id=project_id,
            )
            try:
                record_task_learning(
                    agent_id="qa",
                    task=f"analyze feedback {project_id}",
                    outcome=str(
                        {"created_tickets": created, "summary": result.get("summary", "")}
                    ),
                    success=True,
                )
            except Exception:
                pass
            return {"created_tickets": created, "summary": result.get("summary", "")}
        except Exception as exc:
            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "analyze_feedback_batch",
                input_summary=f"project={project_id}",
                output_summary=str(exc),
                status="error",
                project_id=project_id,
            )
            raise

    def create_ticket_from_report(
        self,
        project_id: str,
        title: str,
        description: str,
        ticket_type: str = "bug",
        priority: str = "medium",
    ) -> dict[str, Any]:
        return self.db.insert(
            "tickets",
            {
                "project_id": project_id,
                "type": ticket_type,
                "priority": priority,
                "title": title,
                "description": description,
                "source": "qa_agent",
                "status": "open",
            },
        )
