"""COO Agent — orchestrateur central ALNUA (CrewAI + Supabase)."""

from __future__ import annotations

import json
import logging
import re
from datetime import date, timedelta
from typing import Any

from crewai import Agent, Crew, LLM, Process, Task
from crewai.tools import tool

from agents.tools.hub_tools import HUB_TOOLS
from database.supabase_client import SupabaseClient, get_supabase
from skills.skill_composio import composio_execute, get_oauth_link

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt officiel du COO
# ---------------------------------------------------------------------------
COO_SYSTEM_PROMPT = """
Tu es le COO d'ALNUA, le bras droit direct d'Emilie.
Elle est seule pour gérer une société avec 3 branches (App, Gaming, Robotique).
Ta mission : protéger son temps et son énergie.

Quand elle te donne une instruction :
1. Identifie le projet concerné (Naïa / Wyrdheim / Eve / ALNUA global)
2. Décompose en sous-tâches concrètes
3. Détermine quel agent est responsable de chaque tâche
4. Retourne un plan d'action en 5 lignes max — jamais de blabla

Agents disponibles sous tes ordres :
- pm_agent : roadmap, tickets, priorisation
- qa_agent : bugs, feedbacks, crash reports
- content_agent : création posts, scripts vidéo, marketing
- brainstorm_agent : idéation, nouveaux produits, features
- spec_agent : génération de prompts Cursor pour le code
- game_director : lore, quêtes, game design, Discord Wyrdheim
- dev_gaming : UE5, Blueprints, C++, Nwiro
- hardware : composants Eve, BOM, architecture robot
- embedded : Raspberry Pi, firmware, naia-embodied, déploiement Eve
- marketing : SEO, communauté, réseaux sociaux, veille

Règles absolues :
- UE5/Unreal → dev_gaming uniquement (jamais dev_app ni spec_agent)
- Toujours confirmer avant une action irréversible (suppression, publication)
- Si tu ne sais pas à quel projet ça appartient, demande
""".strip()

# Alias pour résoudre les noms de projets depuis le langage naturel
PROJECT_ALIASES: dict[str, str] = {
    "naia": "Naïa",
    "naïa": "Naïa",
    "naya": "Naïa",
    "naima": "Naïa",
    "wyrdheim": "Wyrdheim Online",
    "wyrdheim online": "Wyrdheim Online",
    "mmorpg": "Wyrdheim Online",
    "eve": "Eve",
    "robot": "Eve",
    "robotique": "Eve",
    "alnua": "ALNUA",
    "global": "ALNUA",
}

# Mots-clés indiquant une action irréversible
IRREVERSIBLE_KEYWORDS = (
    "publie", "publish", "supprime", "supprimer", "delete", "efface",
    "remove", "envoie le post", "valide la publication",
)


@tool("connect_app_oauth")
def connect_app_oauth(app_name: str) -> str:
    """
    Génère un lien OAuth pour connecter une app externe (Gmail, Notion, Stripe...).
    Envoie le lien à Emilie via Telegram pour qu'elle autorise l'accès.
    app_name: ex. GMAIL, GOOGLECALENDAR, NOTION, STRIPE, SLACK, DISCORD
    """
    link = get_oauth_link(app=app_name, user_id="alnua_coo")
    return f"Lien OAuth pour {app_name}: {link}\nOuvre ce lien pour autoriser l'accès."


@tool("send_email_via_gmail")
def send_email_via_gmail(to: str, subject: str, body: str) -> str:
    """Envoie un email via Gmail. Args: to (destinataire), subject, body."""
    result = composio_execute(
        action="GMAIL_SEND_EMAIL",
        params={"recipient_email": to, "subject": subject, "body": body},
        user_id="alnua_coo",
    )
    return "Email envoyé ✅" if result["success"] else f"Erreur: {result['error']}"


@tool("create_calendar_event")
def create_calendar_event(title: str, date: str, description: str = "") -> str:
    """Crée un événement Google Calendar. date format: '2026-06-15T14:00:00'"""
    result = composio_execute(
        action="GOOGLECALENDAR_CREATE_EVENT",
        params={"summary": title, "start_datetime": date, "description": description},
        user_id="alnua_coo",
    )
    return "Événement créé ✅" if result["success"] else f"Erreur: {result['error']}"

# Instructions clairement liées à un projet
PROJECT_SCOPED_KEYWORDS = (
    "bug", "ticket", "roadmap", "post", "feedback", "feature",
    "crash", "sprint", "priorise", "contenu", "marketing", "spec",
    "cursor", "brainstorm", "idée", "idee",
)

# Ordre important : expressions longues avant sous-chaînes (ex. "raspberry pi" avant "bom")
AGENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "embedded": (
        "raspberry pi", "python pi", "firmware", "ssh eve", "naia-embodied",
        "déployer pi", "deployer pi",
    ),
    "game_director": (
        "wyrdheim", "lore", "quête", "quete", "game design", "level design",
        "économie jeu", "economie jeu", "naïa world", "naia world",
    ),
    "dev_gaming": (
        "blueprint", "c++", "ue5", "unreal", "modding", "websocket ue5",
        "looking glass", "nwiro",
    ),
    "hardware": (
        "composant", "bom", "eve hardware", "circuit", "capteur", "moteur", "servo",
    ),
    "marketing": (
        "seo", "discord", "communauté", "communaute", "réseaux sociaux",
        "reseaux sociaux", "contenu", "tweet", "patch notes", "changelog",
    ),
}


def route_to_agent(
    instruction: str,
    telegram_notify_fn=None,
) -> tuple[str, str | None]:
    """
    Route une instruction vers le bon agent spécialisé.
    Retourne (agent_name, response). response=None si fallback COO.
    """
    instruction_lower = instruction.lower()

    for agent_name, keywords in AGENT_KEYWORDS.items():
        if not any(kw in instruction_lower for kw in keywords):
            continue

        if agent_name == "game_director":
            from agents.game_director_agent import GameDirectorAgent

            return agent_name, GameDirectorAgent(telegram_notify_fn).handle_instruction(
                instruction
            )
        if agent_name == "dev_gaming":
            from agents.dev_gaming_agent import DevGamingAgent

            return agent_name, DevGamingAgent(telegram_notify_fn).handle_instruction(
                instruction
            )
        if agent_name == "hardware":
            from agents.hardware_agent import HardwareAgent

            return agent_name, HardwareAgent(telegram_notify_fn).handle_instruction(
                instruction
            )
        if agent_name == "embedded":
            from agents.embedded_dev_agent import EmbeddedDevAgent

            return agent_name, EmbeddedDevAgent(telegram_notify_fn).handle_instruction(
                instruction
            )
        if agent_name == "marketing":
            from agents.marketing_agent import MarketingAgent

            return agent_name, MarketingAgent(telegram_notify_fn).handle_instruction(
                instruction
            )

    return "coo", None


class COOAgent:
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

    def _build_crew_agent(self) -> Agent:
        assert self._tools is not None and self._llm is not None
        return Agent(
            role="COO ALNUA",
            goal="Orchestrer les agents ALNUA et protéger le temps d'Emilie",
            backstory=COO_SYSTEM_PROMPT,
            tools=self._tools,
            llm=self._llm,
            verbose=self.verbose,
            allow_delegation=False,
            max_iter=12,
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
        ]

    # ------------------------------------------------------------------
    # Accès Supabase (méthodes internes + API publique)
    # ------------------------------------------------------------------
    def _find_project(self, name: str) -> dict[str, Any] | None:
        """Recherche un projet par nom exact ou alias."""
        normalized = name.strip().lower()
        canonical = PROJECT_ALIASES.get(normalized, name.strip())
        if canonical == "ALNUA":
            return None

        projects = self.db.select("projects")
        for project in projects:
            if project["name"].lower() == canonical.lower():
                return project
            if canonical.lower() in project["name"].lower():
                return project
        return None

    def _resolve_project(
        self,
        project: str | None,
        instruction: str,
    ) -> str | None:
        """Résout le projet depuis le paramètre ou l'instruction."""
        if project:
            found = self._find_project(project)
            return found["name"] if found else project

        lowered = instruction.lower()
        for alias, canonical in sorted(
            PROJECT_ALIASES.items(), key=lambda x: len(x[0]), reverse=True
        ):
            if alias in lowered:
                return canonical
        return None

    def _get_project_context_data(self, project_name: str) -> dict[str, Any]:
        """Agrège l'état complet d'un projet."""
        project = self._find_project(project_name)
        if not project:
            raise ValueError(f"Projet introuvable : {project_name}")

        project_id = project["id"]
        open_tickets = self.db.select(
            "tickets",
            filters={"project_id": project_id, "status": "open"},
            order_by="created_at",
            ascending=False,
            limit=10,
        )
        critical = [t for t in open_tickets if t.get("priority") in ("critical", "high")]
        roadmap = self.db.select(
            "roadmap",
            filters={"project_id": project_id},
            order_by="priority",
            ascending=False,
            limit=5,
        )
        new_feedback = self.db.select(
            "feedback",
            filters={"project_id": project_id, "status": "new"},
            limit=5,
        )
        pending_posts = self.db.select(
            "posts_queue",
            filters={"project_id": project_id, "status": "pending_approval"},
            limit=5,
        )
        week_ago = (date.today() - timedelta(days=7)).isoformat()
        analytics = self.db.select(
            "analytics",
            filters={"project_id": project_id},
            order_by="date",
            ascending=False,
            limit=7,
        )
        analytics = [a for a in analytics if a.get("date", "") >= week_ago]

        return {
            "project": project,
            "open_tickets_count": len(open_tickets),
            "critical_tickets": critical,
            "roadmap_top": roadmap,
            "new_feedback_count": len(new_feedback),
            "pending_posts_count": len(pending_posts),
            "recent_analytics": analytics,
        }

    def _format_project_context(self, project_name: str) -> str:
        data = self._get_project_context_data(project_name)
        p = data["project"]
        lines = [
            f"**{p['name']}** ({p['branch']}) — statut {p['status']}",
            f"Tickets ouverts : {data['open_tickets_count']} "
            f"(critiques/hauts : {len(data['critical_tickets'])})",
            f"Feedback nouveau : {data['new_feedback_count']}",
            f"Posts en attente d'approbation : {data['pending_posts_count']}",
        ]
        if data["critical_tickets"]:
            lines.append("Tickets prioritaires :")
            for t in data["critical_tickets"][:3]:
                lines.append(f"  - {t['title']} [{t['priority']}]")
        if data["roadmap_top"]:
            lines.append("Roadmap (top) :")
            for r in data["roadmap_top"][:3]:
                lines.append(f"  - {r['title']} ({r['status']})")
        if data["recent_analytics"]:
            lines.append("Analytics récents :")
            for a in data["recent_analytics"][:3]:
                lines.append(f"  - {a['metric_name']}: {a['value']} ({a['date']})")
        return "\n".join(lines)

    def _fetch_open_tickets(self, project_name: str) -> list[dict[str, Any]]:
        project = self._find_project(project_name)
        if not project:
            raise ValueError(f"Projet introuvable : {project_name}")
        return self.db.select(
            "tickets",
            filters={"project_id": project["id"], "status": "open"},
            order_by="created_at",
            ascending=False,
        )

    def create_task_log(
        self,
        agent: str,
        action: str,
        input_summary: str,
        output_summary: str,
        project_id: str | None = None,
        status: str = "success",
    ) -> dict[str, Any]:
        """Écrit une entrée dans agent_logs."""
        return self.db.insert(
            "agent_logs",
            {
                "agent_name": agent,
                "action": action,
                "project_id": project_id,
                "input_summary": input_summary[:2000],
                "output_summary": output_summary[:2000],
                "status": status,
            },
        )

    _BRANCH_LABELS: dict[str, str] = {
        "app": "App",
        "gaming": "Gaming",
        "robotics": "Robotique",
        "other": "Autre",
    }

    def get_daily_briefing(self) -> dict[str, Any]:
        """Résumé structuré de tous les projets."""
        projects = self.db.select("projects", order_by="branch")
        per_project: list[dict[str, Any]] = []
        summary_lines: list[str] = [f"📋 Briefing ALNUA — {date.today().isoformat()}"]

        total_critical = 0
        total_pending_posts = 0
        total_new_feedback = 0
        urgent_lines: list[str] = []
        branch_ctx: dict[str, list[dict[str, Any]]] = {
            "app": [],
            "gaming": [],
            "robotics": [],
        }

        for project in projects:
            try:
                ctx = self._get_project_context_data(project["name"])
            except Exception as exc:
                logger.warning("Briefing partiel pour %s : %s", project["name"], exc)
                continue

            critical = len(ctx["critical_tickets"])
            pending = ctx["pending_posts_count"]
            feedback = ctx["new_feedback_count"]
            total_critical += critical
            total_pending_posts += pending
            total_new_feedback += feedback

            per_project.append(ctx)
            branch_key = project.get("branch", "other")
            if branch_key in branch_ctx:
                branch_ctx[branch_key].append({"project": project, "ctx": ctx})

            for ticket in ctx["critical_tickets"]:
                urgent_lines.append(
                    f"• [{project['name']}] {ticket['title']} ({ticket['priority']})"
                )

            summary_lines.append(
                f"• {project['name']} ({project.get('status', '?')}) : "
                f"{ctx['open_tickets_count']} tickets, "
                f"{critical} prioritaires, "
                f"{feedback} feedbacks, "
                f"{pending} posts en attente"
            )

        summary_lines.append("")
        summary_lines.append("🏢 Branches :")
        for branch_key in ("app", "gaming", "robotics"):
            label = self._BRANCH_LABELS[branch_key]
            entries = branch_ctx[branch_key]
            if not entries:
                summary_lines.append(f"• {label} : aucun projet actif")
                continue
            open_tickets = sum(e["ctx"]["open_tickets_count"] for e in entries)
            critical_count = sum(len(e["ctx"]["critical_tickets"]) for e in entries)
            names = ", ".join(e["project"]["name"] for e in entries)
            summary_lines.append(
                f"• {label} : {len(entries)} projet(s), "
                f"{open_tickets} tickets, {critical_count} urgent(s) — {names}"
            )

        if urgent_lines:
            summary_lines.append("")
            summary_lines.append("⚡ Tâches urgentes :")
            summary_lines.extend(urgent_lines[:10])
            if len(urgent_lines) > 10:
                summary_lines.append(f"… et {len(urgent_lines) - 10} autre(s)")

        if total_critical:
            summary_lines.append(f"⚠️ {total_critical} ticket(s) critique(s)/haut(s) au total.")
        if total_pending_posts:
            summary_lines.append(f"📣 {total_pending_posts} post(s) à valider.")
        if total_new_feedback:
            summary_lines.append(f"💬 {total_new_feedback} feedback(s) non traité(s).")

        from skills.skill_error_journal import get_open_errors_summary

        errors_summary = get_open_errors_summary()
        if not errors_summary.startswith("✅"):
            summary_lines.append("")
            summary_lines.append("🔴 Journal d'erreurs agents :")
            summary_lines.append(errors_summary)

        summary_lines.append("→ Dis-moi sur quoi tu veux te concentrer aujourd'hui.")

        return {
            "date": date.today().isoformat(),
            "projects": per_project,
            "summary": "\n".join(summary_lines),
        }

    def run_daily_briefing(self) -> str:
        """Compatibilité API / Discord — retourne le briefing formaté."""
        return self.get_daily_briefing()["summary"]

    # ------------------------------------------------------------------
    # Délégation aux sous-agents
    # ------------------------------------------------------------------
    def _require_project(self, project_name: str) -> dict[str, Any]:
        project = self._find_project(project_name)
        if not project:
            raise ValueError(f"Projet introuvable : {project_name}")
        return project

    def _delegate_pm(self, project_name: str, instruction: str = "") -> str:
        from agents.pm_agent import PMAgent

        project = self._require_project(project_name)
        pm = PMAgent(self.db, verbose=self.verbose)
        task = instruction.strip() or f"Triage roadmap et tickets pour {project_name}"
        summary = pm.handle_instruction(task, project["id"])
        self.create_task_log(
            "pm_agent", "handle_instruction", f"{project_name}: {task}", summary, project["id"]
        )
        return summary

    def _delegate_qa(self, project_name: str) -> str:
        from agents.qa_agent import QAAgent

        project = self._require_project(project_name)
        result = QAAgent(self.db).analyze_feedback_batch(project["id"])
        summary = result.get("summary", "Analyse QA terminée.")
        self.create_task_log(
            "qa_agent", "analyze_feedback", project_name, summary, project["id"]
        )
        return summary

    def _delegate_content(self, project_name: str) -> str:
        from agents.content_agent import ContentAgent

        project = self._require_project(project_name)
        posts = ContentAgent(self.db).generate_from_dev_logs(project["id"])
        summary = f"{len(posts)} post(s) généré(s), en attente d'approbation."
        self.create_task_log(
            "content_agent", "generate_from_dev_logs", project_name, summary, project["id"]
        )
        return summary

    def _delegate_brainstorm(self, project_name: str, topic: str) -> str:
        from agents.brainstorm_agent import BrainstormAgent

        project = self._require_project(project_name)
        result = BrainstormAgent(self.db).brainstorm(project["id"], topic)
        ideas = result.get("ideas", [])
        titles = ", ".join(i["title"] for i in ideas[:3]) or "aucune idée"
        summary = f"{len(ideas)} idée(s) : {titles}"
        self.create_task_log(
            "brainstorm_agent", "brainstorm", f"{project_name}: {topic}", summary, project["id"]
        )
        return summary

    def _delegate_spec(self, ticket_id: str) -> str:
        from agents.spec_agent import SpecAgent

        ticket = SpecAgent(self.db).generate_cursor_prompt(ticket_id)
        summary = f"Prompt Cursor généré pour « {ticket.get('title', ticket_id)} »."
        self.create_task_log(
            "spec_agent",
            "generate_cursor_prompt",
            ticket_id,
            summary,
            ticket.get("project_id"),
        )
        return summary

    # ------------------------------------------------------------------
    # Garde-fous
    # ------------------------------------------------------------------
    def _check_irreversible(self, instruction: str) -> str | None:
        lowered = instruction.lower()
        if "confirm" in lowered:
            return None
        for keyword in IRREVERSIBLE_KEYWORDS:
            if keyword in lowered:
                return (
                    f"Action irréversible détectée (« {keyword} »). "
                    "Confirme en incluant le mot « confirm » dans ton instruction."
                )
        return None

    def _needs_project_clarification(self, instruction: str) -> bool:
        lowered = instruction.lower()
        if any(alias in lowered for alias in PROJECT_ALIASES):
            return False
        return any(kw in lowered for kw in PROJECT_SCOPED_KEYWORDS)

    @staticmethod
    def _trim_summary(text: str, max_lines: int = 5) -> str:
        """Force une réponse courte et actionnable."""
        lines = [ln.strip() for ln in text.strip().splitlines() if ln.strip()]
        # Supprime les lignes trop verbeuses (markdown headers vides, etc.)
        cleaned = []
        for ln in lines:
            ln = re.sub(r"^#+\s*", "", ln)
            ln = ln.strip("*- ")
            if ln:
                cleaned.append(ln)
        return "\n".join(cleaned[:max_lines])

    # ------------------------------------------------------------------
    # Point d'entrée principal
    # ------------------------------------------------------------------
    def handle_instruction(self, instruction: str, project: str | None = None) -> str:
        """
        Analyse l'instruction d'Emilie, délègue aux agents concernés,
        logue dans Supabase et retourne un résumé en 3-5 lignes max.
        """
        instruction = instruction.strip()
        if not instruction:
            return "Instruction vide — dis-moi ce que tu veux faire."

        if blocked := self._check_irreversible(instruction):
            self.create_task_log(
                self.AGENT_NAME, "handle_instruction", instruction, blocked, status="pending"
            )
            return blocked

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

        crew_agent = self._ensure_crew()

        task = Task(
            description=(
                f"Instruction d'Emilie : {instruction}\n"
                f"Projet indicatif : {project_name or 'non précisé'}"
                f"{context_block}\n\n"
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


# ---------------------------------------------------------------------------
# CLI de test
# ---------------------------------------------------------------------------
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
        print(f"\n❌ Impossible d'initialiser le COO : {exc}")
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
