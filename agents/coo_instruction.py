"""COO instruction handling — GitHub issues, routing, CrewAI fallback."""
from __future__ import annotations

import logging
import threading
from typing import Any

from crewai import Crew, Process, Task

from agents.coo_composio_tools import create_github_issue_via_composio
from agents.coo_handlers import try_fast_intents
from agents.coo_intents import _needs_plan_execution, detect_coding_intent, detect_target_repo
from agents.coo_routing import route_to_agent
from config.github_repos import get_target_by_slug
from skills.skill_langfuse import trace_agent
from skills.skill_mem0 import recall, remember, should_remember

logger = logging.getLogger(__name__)


class COOInstructionMixin:
    """Requires crew, project, plan, and conversation mixins."""

    def process_message(self, message: str, project: str | None = None) -> dict[str, Any]:
        """
        Handle a COO chat message: auto-create a GitHub issue for coding requests,
        otherwise delegate to the LLM agent.
        """
        message = message.strip()
        if not message:
            return {
                "response": "Instruction vide — dis-moi ce que tu veux faire.",
                "issue_created": False,
            }

        if detect_coding_intent(message):
            repo_slug = detect_target_repo(message)
            target = get_target_by_slug(repo_slug) or get_target_by_slug("hub")
            if target:
                issue = create_github_issue_via_composio(
                    title=message[:80],
                    body=(
                        f"**Demande COO :** {message}\n\n"
                        "*Issue créée automatiquement par le Hub ALNUA.*"
                    ),
                    repo=target.github_repo,
                    labels=["agent-ready"],
                )
                if issue.get("success"):
                    self.create_task_log(
                        self.AGENT_NAME,
                        "create_github_issue",
                        message,
                        f"Issue #{issue['number']} on {target.github_repo}",
                    )
                    return {
                        "response": (
                            f"[OK] Issue #{issue['number']} créée sur "
                            f"`{target.github_repo}` avec le label `agent-ready`.\n"
                            f"Le pipeline va démarrer dans ~30 secondes.\n"
                            f"→ Voir l'issue : {issue['url']}"
                        ),
                        "issue_created": True,
                        "issue_number": issue["number"],
                        "issue_url": issue["url"],
                        "repo": repo_slug,
                    }
                logger.warning(
                    "COO issue creation failed for %s: %s",
                    target.github_repo,
                    issue.get("error"),
                )

        response = self.handle_instruction(message, project)
        return {"response": response, "issue_created": False}

    @trace_agent("coo_agent")
    def handle_instruction(
        self,
        instruction: str,
        project: str | None = None,
        telegram_chat_id: int | None = None,
    ) -> str:
        """
        Analyse l'instruction d'Emilie, délègue aux agents concernés,
        logue dans Supabase et retourne un résumé en 3-5 lignes max.
        """
        instruction = instruction.strip()
        if not instruction:
            return "Instruction vide — dis-moi ce que tu veux faire."

        try:
            self.create_task_log(
                self.AGENT_NAME,
                "handle_instruction",
                instruction,
                "Traitement en cours…",
                status="pending",
            )
        except Exception:
            pass

        fast = try_fast_intents(self, instruction, telegram_chat_id)
        if fast is not None:
            return fast

        if blocked := self._check_irreversible(instruction):
            self.create_task_log(
                self.AGENT_NAME, "handle_instruction", instruction, blocked, status="pending"
            )
            return blocked

        if _needs_plan_execution(instruction):
            return self._execute_plan_pipeline(instruction, project, telegram_chat_id)

        routed_agent, routed_response = route_to_agent(instruction)
        if routed_agent != "coo" and routed_response is not None:
            summary = self._trim_summary(routed_response)
            project_name = self._resolve_project(project, instruction)
            project_id = None
            if project_name and project_name != "ALNUA":
                found = self._find_project(project_name)
                project_id = found["id"] if found else None
            self.create_task_log(
                routed_agent,
                "handle_instruction",
                instruction,
                summary,
                project_id,
            )
            return summary

        project_name = self._resolve_project(project, instruction)
        if project_name is None and self._needs_project_clarification(instruction):
            question = "Sur quel projet ? Naïa, Wyrdheim, Eve ou ALNUA global ?"
            self.create_task_log(
                self.AGENT_NAME, "handle_instruction", instruction, question, status="pending"
            )
            return question

        if telegram_chat_id is not None or not _needs_plan_execution(instruction):
            return self._handle_conversation(
                instruction,
                project_name=project_name,
                telegram_chat_id=telegram_chat_id,
            )

        context_block = ""
        if project_name and project_name != "ALNUA":
            try:
                context_block = (
                    f"\n\nContexte projet ({project_name}) :\n"
                    f"{self._format_project_context(project_name)}"
                )
            except ValueError:
                context_block = f"\n\nProjet mentionné : {project_name} (non trouvé en base)."

        memory_block = ""
        try:
            from skills.skill_agent_learning import get_learning_context

            memory_block = get_learning_context("coo", instruction)
        except Exception:
            memories = recall(instruction)
            if memories:
                memory_block = f"\n\nCONTEXTE MÉMORISÉ :\n{memories}"

        crew_agent = self._ensure_crew()

        task = Task(
            description=(
                f"Instruction d'Emilie : {instruction}\n"
                f"Projet indicatif : {project_name or 'non précisé'}"
                f"{context_block}"
                f"{memory_block}\n\n"
                "Étapes :\n"
                "1. Consulte Supabase si besoin (get_project_context, get_open_tickets, get_daily_briefing)\n"
                "2. Pour créer ticket/roadmap : utilise Lister les projets puis Créer un ticket / "
                "Créer un item roadmap (appels API réels — jamais simuler)\n"
                "3. Sinon délègue via delegate_* (pm_agent pour triage/priorisation)\n"
                "4. Logue chaque action avec create_task_log\n"
                "5. Réponds en 3 à 5 lignes MAX — actionnable, sans blabla"
            ),
            expected_output=(
                "Résumé en 3 à 5 lignes maximum, en français, "
                "avec les actions lancées et la prochaine étape pour Emilie."
            ),
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
            raw = result.raw if hasattr(result, "raw") else str(result)
            summary = self._trim_summary(raw)

            project_id = None
            if project_name and project_name != "ALNUA":
                found = self._find_project(project_name)
                project_id = found["id"] if found else None

            self.create_task_log(
                self.AGENT_NAME,
                "handle_instruction",
                instruction,
                summary,
                project_id,
            )

            if should_remember(instruction):
                remember(f"Emilie a dit : {instruction}", agent_id="coo")

            try:
                from agents.skill_synthesizer import maybe_synthesize_skill

                threading.Thread(
                    target=maybe_synthesize_skill,
                    args=(instruction, summary),
                    daemon=True,
                ).start()
            except Exception:
                pass

            try:
                from skills.skill_agent_learning import learn_from_outcome

                learn_from_outcome(
                    agent_id="coo",
                    task=instruction,
                    outcome=summary,
                    success=True,
                )
            except Exception:
                pass

            return summary

        except Exception as exc:
            logger.exception("Erreur COO handle_instruction")
            error_msg = f"Erreur COO : {exc}"
            self.create_task_log(
                self.AGENT_NAME,
                "handle_instruction",
                instruction,
                error_msg,
                status="error",
            )
            return "Une erreur est survenue. Réessaie ou vérifie la connexion Supabase/OpenRouter."
