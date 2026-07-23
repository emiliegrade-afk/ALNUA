"""
agents/dev_app_agent.py

Agent CrewAI — Dev App (Lead Dev + Backend + Frontend/Mobile)

Responsabilités :
- Développement Naïa App (React Native + Supabase)
- Développement Eve Journey's app
- PRs automatiques depuis backlog GitHub
- Code Review (validation qualité avant merge)
- Debugging builds CI

Tools : skill_coding_agent, skill_gh_issues, skill_playwright, skill_git, skill_model_usage
Règle : max 6 tools. Ne touche pas aux projets Gaming ou Robotique.
"""

from __future__ import annotations

import json
import logging

from crewai import Agent, Crew, LLM, Task
from crewai.tools import tool

from skills.skill_coding_agent import execute_coding_task
from skills.skill_composio import get_composio_tools
from config.agent_operating_spec import crew_backstory
from skills.skill_gh_issues import comment_on_issue, get_issue, get_open_issues, list_ready_issues, process_issue
from skills.skill_langfuse import trace_agent
from skills.skill_model_usage import format_costs_report
from skills.skill_playwright import run_and_report

logger = logging.getLogger(__name__)

_telegram_notify = None


def _build_llm() -> LLM:
    from agents.base import build_crewai_llm

    return build_crewai_llm("dev_app", temperature=0.3)


@tool("coding_agent")
def coding_agent_tool(spec_json: str) -> str:
    """
    Lance le pipeline de codage autonome sur une spec JSON.
    Input : JSON string avec task_id, title, description, repo_path, branch_name.
    Output : URL de la PR créée ou message d'erreur.
    """
    try:
        spec = json.loads(spec_json)
        result = execute_coding_task(spec, telegram_notify_fn=_telegram_notify)
        if result["success"]:
            return f"[OK] PR créée : {result['pr_url']}"
        return f"[ERREUR] Échec : {result['error']}"
    except Exception as e:
        return f"[ERREUR] Erreur tool coding_agent : {e}"


@tool("list_ready_issues")
def list_issues_tool(dummy: str = "") -> str:
    """
    Liste les GitHub Issues prêtes (label 'agent-ready').
    Retourne JSON avec numéro, titre, et description de chaque issue.
    """
    try:
        issues = list_ready_issues()
        if not issues:
            return "Aucune issue prête à traiter."
        return json.dumps(
            [
                {
                    "number": i["number"],
                    "title": i["title"],
                    "body": i.get("body", "")[:200],
                    "repo_slug": i.get("_repo_slug"),
                    "repo_name": i.get("_repo_name"),
                }
                for i in issues
            ],
            ensure_ascii=False,
            indent=2,
        )
    except Exception as e:
        return f"[ERREUR] Erreur : {e}"


@tool("run_qa_tests")
def qa_tests_tool(input_json: str) -> str:
    """
    Lance les tests QA sur une branche/PR.
    Input JSON : {"branch": "feat/...", "pr_number": 42, "repo_path": "/path/to/repo"}
    """
    try:
        data = json.loads(input_json)
        result = run_and_report(
            repo_path=data["repo_path"],
            branch=data["branch"],
            pr_number=data["pr_number"],
        )
        status = "[OK] Passés" if result["passed"] else "[ERREUR] Échoués"
        return (
            f"{status} — {result['passed_count']}/{result['total']} tests "
            f"en {result['duration_s']}s"
        )
    except Exception as e:
        return f"[ERREUR] Erreur tests : {e}"


@tool("get_costs_report")
def costs_report_tool(period: str = "day") -> str:
    """
    Retourne un rapport des coûts LLM.
    period : 'day' pour aujourd'hui, 'month' pour le mois en cours.
    """
    return format_costs_report(period)


class DevAppAgent:
    def __init__(self, telegram_notify_fn=None):
        global _telegram_notify
        _telegram_notify = telegram_notify_fn
        self.telegram_notify = telegram_notify_fn
        self.agent = Agent(
            role="Dev App Agent",
            goal=(
                "Implémenter les features et corrections demandées sur les projets App "
                "(Naïa App, Eve Journey's). Créer des PRs propres, documentées, avec tests. "
                "Respecter les conventions ALNUA : logging, gestion d'erreurs, docstrings."
            ),
            backstory=crew_backstory("dev_app"),
            tools=[
                coding_agent_tool,
                list_issues_tool,
                qa_tests_tool,
                costs_report_tool,
                *get_composio_tools(agent_name="dev_app_agent", user_id="alnua_dev_app"),
                get_open_issues,
                comment_on_issue,
            ],
            llm=_build_llm(),
            max_iter=10,
            verbose=True,
        )

    @trace_agent("dev_app_agent")
    def handle_instruction(self, instruction: str) -> str:
        """
        Point d'entrée : reçoit une instruction en langage naturel du COO ou de Telegram.
        """
        from skills.skill_agent_learning import (
            get_learning_context,
            record_task_learning,
        )

        memory_block = get_learning_context("dev_app", instruction)
        task = Task(
            description=instruction + memory_block,
            agent=self.agent,
            expected_output="Résultat de la tâche avec liens PR/commit si applicable.",
        )

        crew = Crew(agents=[self.agent], tasks=[task])
        result = str(crew.kickoff())
        try:
            record_task_learning(agent_id="dev_app", task=instruction, outcome=result)
        except Exception:
            pass
        return result

    def process_ready_issues(self):
        """
        Traite toutes les issues GitHub labelées "agent-ready".
        À appeler depuis le scheduler ou manuellement.
        """
        issues = list_ready_issues()
        if not issues:
            logger.info("[DevApp] Aucune issue à traiter")
            return

        for issue in issues:
            process_issue(issue, telegram_notify_fn=self.telegram_notify)

    def process_issue_by_number(
        self, issue_number: int, repo_slug: str | None = None
    ) -> dict:
        """Traite une issue GitHub spécifique par son numéro (et repo si fourni)."""
        issue = get_issue(issue_number, repo_slug=repo_slug)
        return process_issue(issue, telegram_notify_fn=self.telegram_notify)
