"""COO Agent — orchestrateur central ALNUA (CrewAI + Supabase)."""

from __future__ import annotations

import logging
from typing import Any

from crewai import Agent, Crew, LLM, Process, Task
from crewai.tools import tool

from agents.tools.hub_tools import HUB_TOOLS
from config.llm_runtime import CREWAI_MAX_ITER_COO
from database.supabase_client import SupabaseClient, get_supabase
from config.github_repos import get_target_by_slug
from skills.skill_composio import get_composio_tools
from skills.skill_gh_issues import create_github_issue, get_open_issues
from skills.skill_langfuse import trace_agent
from skills.skill_mem0 import recall, remember, should_remember
from skills.skill_supabase import fetch_project_summary

logger = logging.getLogger(__name__)

from agents.coo_briefing import COOBriefingMixin
from agents.coo_composio_tools import (  # noqa: F401 — re-export façade
    connect_app_oauth,
    create_calendar_event,
    create_github_issue_via_composio,
    search_knowledge_base,
    send_email_via_gmail,
)
from agents.coo_constants import (  # noqa: F401 — re-export façade
    COO_SYSTEM_PROMPT,
    IRREVERSIBLE_KEYWORDS,
    PROJECT_ALIASES,
    PROJECT_SCOPED_KEYWORDS,
)
from agents.coo_delegates import COODelegatesMixin
from agents.coo_handlers import try_fast_intents
from agents.coo_intents import (  # noqa: F401 — re-export façade
    CODING_KEYWORDS,
    RND_KEYWORDS,
    RESEARCH_KEYWORDS,
    TEACH_KEYWORDS,
    _detect_research_intent,
    _detect_teach_intent,
    _extract_research_topic,
    _format_plan_execution_result,
    _is_standalone_rnd_research,
    _needs_plan_execution,
    detect_coding_intent,
    detect_target_repo,
)
from agents.coo_plan import COOPlanMixin
from agents.coo_project import COOProjectMixin
from agents.coo_routing import AGENT_KEYWORDS, route_to_agent  # noqa: F401


class COOAgent(
    COOProjectMixin,
    COOBriefingMixin,
    COODelegatesMixin,
    COOPlanMixin,
):
    """Agent COO — point d'entrée unique d'Emilie vers le système ALNUA."""

    AGENT_NAME = "coo_agent"

    def __init__(
        self,
        db: SupabaseClient | None = None,
        verbose: bool = False,
    ) -> None:
        self.db = db or get_supabase()
        self.verbose = verbose
        self._llm: LLM | None = None
        self._tools: list | None = None
        self._crew_agent: Agent | None = None

    def _ensure_crew(self) -> Agent:
        """Initialise CrewAI uniquement pour handle_instruction (pas le briefing)."""
        if self._crew_agent is None:
            self._llm = self._build_llm()
            self._tools = self._build_tools()
            self._crew_agent = self._build_crew_agent()
        return self._crew_agent

    # ------------------------------------------------------------------
    # Configuration CrewAI
    # ------------------------------------------------------------------
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

        # Exécution réelle via plan_executor (évite les réponses CrewAI sans action)
        if _needs_plan_execution(instruction):
            return self._execute_plan_pipeline(instruction, project, telegram_chat_id)

        # Routage vers agents spécialisés Phase 3
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

        # Chat rapide (Telegram + questions sans exécution lourde) — toujours une réponse claire
        if telegram_chat_id is not None or not _needs_plan_execution(instruction):
            return self._handle_conversation(
                instruction,
                project_name=project_name,
                telegram_chat_id=telegram_chat_id,
            )

        # Contexte injecté pour guider le COO
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

            # Auto-skill generation — boucle d'apprentissage (non-bloquant)
            try:
                from agents.skill_synthesizer import maybe_synthesize_skill
                import threading
                threading.Thread(
                    target=maybe_synthesize_skill,
                    args=(instruction, summary),
                    daemon=True,
                ).start()
            except Exception:
                pass  # Never block the COO for this

            # Apprentissage COO — distille une leçon de chaque instruction traitée
            try:
                from skills.skill_agent_learning import learn_from_outcome
                learn_from_outcome(
                    agent_id="coo",
                    task=instruction,
                    outcome=summary,
                    success=True,
                )
            except Exception:
                pass  # Never block the COO for this

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

    def _handle_conversation(
        self,
        instruction: str,
        *,
        project_name: str | None = None,
        telegram_chat_id: int | None = None,
    ) -> str:
        """Réponse chat rapide — pas de CrewAI (évite les silences Telegram)."""
        from services.secretary_intents import build_academy_status_brief
        from services.telegram_chat_memory import get_context_block
        from services.telegram_presence import CANNOT_DO_ARIA, hub_online

        history = get_context_block(telegram_chat_id)
        academy = build_academy_status_brief()
        hub_line = "Hub en ligne." if hub_online() else "Hub ARRÊTÉ."

        memory_block = ""
        try:
            from skills.skill_agent_learning import get_learning_context

            memory_block = get_learning_context("coo", instruction)
        except Exception:
            pass

        prompt = f"""Emilie (CEO) t'écrit :
{instruction}

{history}

Projet indicatif : {project_name or "non précisé"}
État technique : {hub_line}

Contexte Academy / ops :
{academy[:1500]}

{memory_block}

Réponds comme Aria Voss, COO d'ALNUA — tutoiement, 3 à 8 phrases, français.
Sois directe et actionnable. Si tu ne peux pas exécuter : dis-le clairement et propose une alternative.
Si la demande concerne mails/agenda → renvoie vers Nadia.
Pas de markdown lourd — texte lisible sur Telegram."""

        try:
            from agents.base import LLMClient

            raw = LLMClient().complete(
                COO_SYSTEM_PROMPT,
                prompt,
                agent_id=self.AGENT_NAME,
                temperature=0.45,
            )
            text = (raw or "").strip()
            if not text:
                text = CANNOT_DO_ARIA
        except Exception as exc:
            logger.warning("coo conversation failed: %s", exc)
            text = (
                "Je n'ai pas pu répondre (IA ou Hub indisponible).\n\n"
                + CANNOT_DO_ARIA
            )

        try:
            self.create_task_log(
                self.AGENT_NAME, "handle_instruction", instruction, text[:300]
            )
        except Exception:
            pass
        return self._trim_summary(text)


def main() -> None:
    """Boucle interactive pour tester le COO depuis le terminal."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    print("=" * 50)
    print("  ALNUA Hub — Agent COO")
    print("  Parle-moi en langage naturel.")
    print("  Commandes : briefing | exit")
    print("=" * 50)

    try:
        coo = COOAgent(verbose=True)
    except Exception as exc:
        print(f"\n[ERREUR] Impossible d'initialiser le COO : {exc}")
        print("Vérifie ton fichier .env (SUPABASE_URL, SUPABASE_KEY, OPENROUTER_API_KEY).")
        return

    while True:
        try:
            user_input = input("\nEmilie > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nÀ plus.")
            break

        if not user_input:
            continue

        lowered = user_input.lower()
        if lowered in ("exit", "quit", "q"):
            print("COO > Bonne session. À demain.")
            break

        if lowered == "briefing":
            try:
                print(f"\nCOO >\n{coo.run_daily_briefing()}")
            except Exception as exc:
                print(f"\nCOO > Erreur briefing : {exc}")
            continue

        try:
            response = coo.handle_instruction(user_input)
            print(f"\nCOO > {response}")
        except Exception as exc:
            print(f"\nCOO > Erreur : {exc}")


if __name__ == "__main__":
    main()
