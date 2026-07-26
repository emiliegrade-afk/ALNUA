"""QA Agent — analyzes feedback and crash reports, creates tickets."""

from __future__ import annotations

from agents.agent_base import AgentBase

from typing import Any

from crewai import Agent, LLM

from agents.base import LLMClient, log_agent_action, parse_json_response
from agents.tools.hub_tools import QA_TOOLS
from config.agent_operating_spec import get_system_prompt
from database.supabase_client import SupabaseClient
from skills.skill_langfuse import trace_agent


class QAAgent(AgentBase):
    AGENT_NAME = "qa_agent"

    SYSTEM_PROMPT = get_system_prompt("qa")

    def __init__(
        self,
        db: SupabaseClient | None = None,
        llm: LLMClient | None = None,
    ) -> None:
        super().__init__(db, llm)
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
            raw = self._complete(user_prompt, temperature=0.2)
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

    @trace_agent("qa_agent")
    def review_diff(
        self,
        diff_summary: str,
        context: str = "",
        files_changed: list[str] | None = None,
    ) -> dict[str, Any]:
        """Gate QA senior obligatoire avant tout merge d'intégration (dev_integrator délègue ici)."""
        from skills.skill_agent_learning import inject_learning_context, record_task_learning

        if not diff_summary.strip():
            return {"verdict": "approved", "score": 10, "issues": [], "summary": "Diff vide — rien à review."}

        prompt = inject_learning_context(
            f"""Effectue une review QA senior AVANT un merge d'intégration multi-agents.
Sois exigeante : en cas de doute, choisis "changes_requested" plutôt que "approved".
Contexte : {context or 'Intégration multi-agents'}
Branches/fichiers concernés : {files_changed or 'non précisé'}

```diff
{diff_summary[:12000]}
```

Réponds en JSON :
{{
  "verdict": "approved|changes_requested|rejected",
  "score": 7,
  "issues": [
    {{ "severity": "critical|major|minor", "file": "string", "description": "string", "fix": "string" }}
  ],
  "security_flags": ["secrets exposés, injection, etc."],
  "summary": "Verdict en une phrase"
}}

Règles :
- "rejected" si régression fonctionnelle probable, secret exposé, ou faille de sécurité.
- "changes_requested" si issues majeures non bloquantes mais à corriger avant merge.
- "approved" seulement si aucune issue critical/major.""",
            "qa", context or "review_diff",
        )
        raw = self._complete(prompt, temperature=0.15, max_tokens=3000)
        result = parse_json_response(raw)
        result.setdefault("verdict", "changes_requested")

        log_agent_action(
            self.db, self.AGENT_NAME, "review_diff",
            input_summary=(context or "diff review")[:200],
            output_summary=f"verdict={result.get('verdict')} score={result.get('score')}",
            status="success",
        )
        try:
            record_task_learning(
                agent_id="qa",
                task=f"review_diff {context}"[:200],
                outcome=str(result),
                success=result.get("verdict") == "approved",
            )
        except Exception:
            pass
        return result
