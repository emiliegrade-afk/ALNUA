"""COO Agent — orchestrateur central ALNUA (CrewAI + Supabase)."""

from __future__ import annotations

import logging
import re
from datetime import date, timedelta
from typing import Any

from crewai import Agent, Crew, LLM, Process, Task
from crewai.tools import tool

from agents.tools.hub_tools import HUB_TOOLS
from config.agent_operating_spec import get_system_prompt
from config.llm_runtime import CREWAI_MAX_ITER_COO
from database.supabase_client import SupabaseClient, get_supabase
from config.github_repos import get_target_by_slug
from skills.skill_chroma import search_knowledge as _search
from skills.skill_composio import composio_execute, get_composio_tools, get_oauth_link
from skills.skill_gh_issues import create_github_issue, get_open_issues
from skills.skill_langfuse import trace_agent
from skills.skill_mem0 import recall, remember, should_remember
from skills.skill_supabase import fetch_project_summary

logger = logging.getLogger(__name__)

CODING_KEYWORDS = (
    "code", "crée", "cree", "développe", "developpe", "ajoute", "implémente",
    "implemente", "fix", "corrige", "répare", "repare", "refactorise",
    "optimise", "feature", "fonctionnalité", "fonctionnalite", "écran", "ecran",
    "page", "composant",
)

RESEARCH_KEYWORDS = (
    "recherche", "veille", "renseigne", "cherche sur", "trouve des infos",
    "mets à jour", "apprends", "investiguer", "investigue",
)
TEACH_KEYWORDS = ("apprends à", "enseigne", "dis à", "informe", "leçon pour", "donne cette info")
RND_KEYWORDS = ("explore l'idée", "idée r&d", "lance un cycle r&d", "rapport r&d", "meilleures idées", "fil conducteur r&d", "change le focus r&d")

# Instructions qui doivent déclencher une exécution réelle (plan_executor), pas du blabla CrewAI.
_PLAN_EXECUTION_MARKERS = (
    "faisabilité", "faisabilite", "roi", "retour sur investissement", "rentabilité",
    "analyse", "étude", "etude", "évalue", "evalue", "prépare", "prepare",
    "lance", "délègue", "delegue", "organise", "planifie", "campagne",
    "stratégie", "strategie", "priorise", "triage", "génère un", "genere un",
    "brief", "étude de marché", "market analysis",
    "relance", "relancer", "réveille", "reveille",
)
_BRIEF_ONLY_MARKERS = (
    "urgent aujourd", "qu'est-ce qui est urgent", "état des projets",
    "statut des projets", "briefing du jour", "résumé du jour",
)


def _is_standalone_rnd_research(instruction: str) -> bool:
    """True when the message is R&D/veille without an explicit product target."""
    lower = instruction.lower()
    rnd_markers = (
        "r&d", "rnd", "investiguer", "investigue", "veille sur", "recherche pour r",
        "recherche r&d", "cycle r&d", "fil conducteur r&d",
    )
    product_markers = (
        "nuaway", "nomad", "vanlife", "park4night", "naïa", "naia",
        "wyrdheim", "eve", "creatorflow",
    )
    return any(m in lower for m in rnd_markers) and not any(m in lower for m in product_markers)


def _needs_plan_execution(instruction: str) -> bool:
    """True when the COO must run agents for real, not only chat."""
    lower = instruction.lower()
    if any(kw in lower for kw in _BRIEF_ONLY_MARKERS):
        return False
    return any(kw in lower for kw in _PLAN_EXECUTION_MARKERS)


def _format_plan_execution_result(result: dict[str, Any]) -> str:
    """Turn plan_executor output into a short COO reply."""
    if result.get("error") and not result.get("results"):
        return f"❌ Plan non exécuté : {result['error']}"

    lines = [f"✅ Plan exécuté — {result.get('title', 'objectif')}"]
    for step in result.get("results", [])[:6]:
        agent = step.get("agent_id", "?")
        desc = step.get("description", "")[:60]
        if step.get("success"):
            lines.append(f"• {agent} : {desc} ✓")
        else:
            err = (step.get("error") or "échec")[:80]
            lines.append(f"• {agent} : {desc} — {err}")

    failed = result.get("failure_count", 0)
    if failed:
        lines.append(f"\n⚠️ {failed} étape(s) en échec — vérifie les logs agents.")
    return "\n".join(lines)[:3500]


def _detect_research_intent(msg: str) -> tuple[bool, str | None]:
    """Détecte si l'instruction est une demande de recherche web. Retourne (bool, agent_cible)."""
    msg_lower = msg.lower()
    if not any(kw in msg_lower for kw in RESEARCH_KEYWORDS):
        return False, None
    # Cherche un agent cible dans le message
    agent_map = {
        "marketing": "marketing_agent", "contenu": "content_agent", "content": "content_agent",
        "hardware": "hardware_agent", "embedded": "embedded_dev", "comptable": "accountant_agent",
        "dev app": "dev_app", "dev gaming": "dev_gaming", "game director": "game_director",
        "rnd": "rnd_agent", "r&d": "rnd_agent", "pm": "pm_agent",
    }
    for keyword, agent_id in agent_map.items():
        if keyword in msg_lower:
            return True, agent_id
    return True, None  # recherche générale


def _extract_research_topic(instruction: str, agent_id: str | None) -> str | None:
    """Pull a custom topic from a veille/recherche message when present."""
    raw = instruction.strip()
    if not raw:
        return None

    patterns = (
        r"recherche(?:r)?\s+(?:pour\s+)?(?:r&?d|rnd)\s*[:.]?\s*(.+)$",
        r"recherche(?:r)?\s+(?:sur\s+)?(.+)$",
        r"veille\s+(?:sur\s+)?(.+)$",
        r"investiguer\s+(?:sur\s+)?(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.I)
        if match:
            topic = match.group(1).strip(" :.-")
            # Strip trailing agent name if duplicated
            topic = re.sub(r"\s+pour\s+(marketing|r&?d|rnd|pm).*$", "", topic, flags=re.I)
            if len(topic) >= 4:
                return topic

    if agent_id:
        return None
    return None


def _detect_teach_intent(msg: str) -> tuple[bool, str | None, str | None]:
    """Détecte si l'instruction est une leçon à injecter. Retourne (bool, agent_cible, contenu)."""
    msg_lower = msg.lower()
    if not any(kw in msg_lower for kw in TEACH_KEYWORDS):
        return False, None, None
    agent_map = {
        "marketing": "marketing_agent", "contenu": "content_agent",
        "hardware": "hardware_agent", "embedded": "embedded_dev",
        "comptable": "accountant_agent", "dev": "dev_app",
    }
    target = None
    for keyword, agent_id in agent_map.items():
        if keyword in msg_lower:
            target = agent_id
            break
    return True, target, msg


def detect_coding_intent(message: str) -> bool:
    """True when the message looks like a dev/coding request."""
    msg = message.lower()
    return any(kw in msg for kw in CODING_KEYWORDS)


def detect_target_repo(message: str) -> str:
    """Resolve repo slug (hub / naia / nomad) from message context."""
    msg = message.lower()
    if "naïa" in msg or "naia" in msg:
        return "naia"
    if "nomad" in msg or "nuaway" in msg:
        return "nomad"
    if any(k in msg for k in ("hub alnua", "alnua hub", "infra interne", "repo hub", "sur le hub")):
        return "hub"
    return "hub"


def create_github_issue_via_composio(
    title: str,
    body: str,
    repo: str,
    labels: list[str] | None = None,
    user_id: str = "alnua_coo",
) -> dict[str, Any]:
    """Create a GitHub issue via Composio; returns {number, url, success}."""
    owner, _, repo_name = repo.partition("/")
    if not repo_name:
        return {"success": False, "error": f"Invalid repo slug: {repo}"}

    result = composio_execute(
        action="GITHUB_CREATE_AN_ISSUE",
        params={
            "owner": owner,
            "repo": repo_name,
            "title": title,
            "body": body or "Issue créée par le COO ALNUA.",
            "labels": labels or ["agent-ready"],
        },
        user_id=user_id,
    )
    if not result["success"]:
        return {"success": False, "error": result.get("error")}

    data = result.get("data") or {}
    if not isinstance(data, dict):
        data = {}

    number = data.get("number")
    url = data.get("html_url")
    if number is None or not url:
        nested = data.get("response_data") or data.get("data") or {}
        if isinstance(nested, dict):
            number = number or nested.get("number")
            url = url or nested.get("html_url")

    if number is None or not url:
        return {
            "success": False,
            "error": "GitHub issue created but response missing number/url",
        }

    return {"number": number, "url": url, "success": True}

# ---------------------------------------------------------------------------
# System prompt officiel du COO
# ---------------------------------------------------------------------------
COO_SYSTEM_PROMPT = get_system_prompt("coo").strip()

# Alias pour résoudre les noms de projets depuis le langage naturel
PROJECT_ALIASES: dict[str, str] = {
    "naia": "Naïa",
    "naïa": "Naïa",
    "naya": "Naïa",
    "naima": "Naïa",
    "nuaway": "NUAWAY",
    "nuway": "NUAWAY",
    "nomad": "NUAWAY",
    "nomads": "NUAWAY",
    "vanlife": "NUAWAY",
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
    return "Email envoyé [OK]" if result["success"] else f"Erreur: {result['error']}"


@tool("create_calendar_event")
def create_calendar_event(title: str, date: str, description: str = "") -> str:
    """Crée un événement Google Calendar. date format: '2026-06-15T14:00:00'"""
    result = composio_execute(
        action="GOOGLECALENDAR_CREATE_EVENT",
        params={"summary": title, "start_datetime": date, "description": description},
        user_id="alnua_coo",
    )
    return "Événement créé [OK]" if result["success"] else f"Erreur: {result['error']}"


@tool("search_knowledge_base")
def search_knowledge_base(query: str) -> str:
    """Cherche dans la base de connaissance ALNUA (specs, docs, notes)."""
    results = _search(query)
    if not results:
        return "Aucun document trouvé pour cette recherche."
    return "\n---\n".join(results[:3])

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
        if not errors_summary.startswith("[OK]"):
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
    # Plan executor — exécution réelle multi-agents
    # ------------------------------------------------------------------
    def _execute_plan_pipeline(
        self,
        instruction: str,
        project: str | None,
        telegram_chat_id: int | None,
    ) -> str:
        """Décompose l'objectif en plan COO et exécute les agents (pas de blabla)."""
        import threading

        project_name = self._resolve_project(project, instruction) or "ALNUA"
        if _is_standalone_rnd_research(instruction):
            project_name = "ALNUA"
            context = (
                f"Instruction R&D (hors produit, ne pas créer de tickets sur NUAWAY/Naïa) : "
                f"{instruction[:500]}"
            )
        else:
            context = f"Projet : {project_name}. Instruction Emilie : {instruction[:500]}"

        def _run() -> dict[str, Any]:
            from services.plan_executor import run_coo_plan

            return run_coo_plan(instruction, context)

        if telegram_chat_id is not None:
            ack = (
                "✅ Plan d'action lancé — les agents exécutent les étapes.\n"
                "Je t'envoie le résumé ici dès que c'est terminé."
            )

            def _worker() -> None:
                try:
                    result = _run()
                    summary = _format_plan_execution_result(result)
                    self.create_task_log(
                        self.AGENT_NAME,
                        "plan_execution",
                        instruction,
                        summary[:2000],
                    )
                    from skills.skill_telegram_notify import notify_telegram

                    notify_telegram(summary, chat_id=telegram_chat_id)
                except Exception as exc:
                    logger.exception("COO plan_execution background failed")
                    err = f"❌ Exécution du plan échouée : {exc}"
                    try:
                        self.create_task_log(
                            self.AGENT_NAME,
                            "plan_execution",
                            instruction,
                            err[:500],
                            status="error",
                        )
                    except Exception:
                        pass
                    from skills.skill_telegram_notify import notify_telegram

                    notify_telegram(err, chat_id=telegram_chat_id)

            threading.Thread(
                target=_worker,
                daemon=False,
                name=f"coo-plan-{instruction[:24]}",
            ).start()
            return ack

        try:
            result = _run()
            summary = _format_plan_execution_result(result)
            project_id = None
            if project_name != "ALNUA":
                found = self._find_project(project_name)
                project_id = found["id"] if found else None
            self.create_task_log(
                self.AGENT_NAME,
                "plan_execution",
                instruction,
                summary[:2000],
                project_id,
            )
            return summary
        except Exception as exc:
            logger.exception("COO plan_execution failed")
            err = f"❌ Exécution du plan échouée : {exc}"
            self.create_task_log(
                self.AGENT_NAME,
                "plan_execution",
                instruction,
                err[:500],
                status="error",
            )
            return err

    # ------------------------------------------------------------------
    # Point d'entrée principal
    # ------------------------------------------------------------------
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

        msg_lower = instruction.lower()

        # Investigation R&D sur un sujet libre (Telegram NL)
        from services.coo_telegram_intents import (
            capture_idea,
            detect_idea_capture,
            detect_rnd_investigation,
            extract_investigation_query,
            launch_rnd_investigation,
        )

        if detect_rnd_investigation(instruction):
            topic = extract_investigation_query(instruction)
            if topic:
                ack = launch_rnd_investigation(topic, chat_id=telegram_chat_id)
                try:
                    self.create_task_log(
                        self.AGENT_NAME, "rnd_investigation", instruction, ack[:200]
                    )
                except Exception:
                    logger.warning("coo: task log rnd_investigation failed", exc_info=True)
                return ack

        # Boîte à idées — capture NL sans formule magique
        if detect_idea_capture(instruction):
            try:
                idea = capture_idea(instruction, source="Emilie via COO")
                title = idea.get("title", instruction[:80])
                ack = (
                    f"💡 Idée enregistrée dans le Centre R&D\n"
                    f"{title[:100]}\n"
                    f"Visible dans Propositions — brainstorm ou promote quand tu veux."
                )
                self.create_task_log(self.AGENT_NAME, "idea_capture", instruction, ack[:200])
                return ack
            except ValueError:
                return "❌ Idée vide — précise ce que tu veux garder."

        from services.secretary_intents import (
            build_academy_status_brief,
            detect_academy_intent,
            detect_wake_ops,
        )

        if detect_wake_ops(instruction):
            from services.agent_wake import wake_agents

            result = wake_agents(notify=False, retry_failed=True)
            ack = f"✅ Pipeline Academy relancé — Théo reprend le codage.\n{result.get('summary', '')}"
            try:
                self.create_task_log(self.AGENT_NAME, "wake_agents", instruction, ack[:200])
            except Exception:
                pass
            return ack

        if detect_academy_intent(instruction):
            brief = build_academy_status_brief()
            try:
                self.create_task_log(self.AGENT_NAME, "academy_status", instruction, brief[:200])
            except Exception:
                pass
            return brief

        # Commandes R&D
        if any(kw in msg_lower for kw in RND_KEYWORDS):
            from agents.rnd_center import run_rnd_cycle, inject_idea, set_vision, get_top_ideas
            if "explore l'idée" in msg_lower or "idée r&d" in msg_lower:
                from services.coo_telegram_intents import extract_idea_text

                body = extract_idea_text(instruction) or instruction
                inject_idea(body, source="Emilie via COO")
                return f"💡 Idée ajoutée au pipeline R&D : \"{body[:80]}...\" — sera évaluée au prochain cycle."
            elif "fil conducteur" in msg_lower or "focus r&d" in msg_lower:
                set_vision(instruction)
                return "🎯 Fil conducteur R&D mis à jour."
            elif "meilleures idées" in msg_lower or "rapport r&d" in msg_lower:
                top = get_top_ideas(limit=5)
                if not top:
                    return "Aucune idée R&D évaluée pour l'instant. Lance un cycle : 'lance un cycle R&D'."
                lines = ["🏆 Top idées R&D ALNUA :"]
                for i, idea in enumerate(top, 1):
                    lines.append(f"{i}. [{idea.get('domain','?').upper()}] {idea['title']} — score {idea.get('score','?')}/30 ({idea.get('verdict','?')})")
                    lines.append(f"   {idea.get('description','')[:100]}")
                return "\n".join(lines)
            else:
                run_rnd_cycle(blocking=False)
                return "🧪 Cycle R&D lancé — rapport dans quelques minutes sur Telegram."

        # Recherche web → bibliothèque des bureaux
        is_research, research_agent = _detect_research_intent(instruction)
        if is_research:
            from services.bureau_library import bureau_for_agent, run_bureau_research

            topic = _extract_research_topic(instruction, research_agent)
            if research_agent == "rnd_agent" and topic and len(topic) >= 4:
                ack = launch_rnd_investigation(topic, chat_id=telegram_chat_id)
                try:
                    self.create_task_log(
                        self.AGENT_NAME, "rnd_investigation", instruction, ack[:200]
                    )
                except Exception:
                    logger.warning("coo: task log rnd_investigation failed", exc_info=True)
                return ack
            query = topic or instruction.strip()[:400]
            bureaus = [bureau_for_agent(research_agent)] if research_agent else None
            result = run_bureau_research(
                query,
                bureaus=bureaus,
                requested_by="aria",
                blocking=telegram_chat_id is None,
                notify_chat_id=telegram_chat_id,
            )
            try:
                self.create_task_log(
                    self.AGENT_NAME, "library_research", instruction, result.get("message", "")[:200]
                )
            except Exception:
                pass
            if telegram_chat_id is None and result.get("entries_saved") is not None:
                n = result.get("entries_saved", 0)
                return (
                    f"📚 **Recherche terminée** — « {query} »\n\n"
                    f"**{n}** fiche(s) rangée(s) dans la bibliothèque (rien supprimé)."
                )
            return f"📚 {result.get('message', 'Recherche lancée.')}"

        # Commande d'injection de leçon — "apprends au marketing_agent que les Reels < 30s performent mieux"
        is_teach, teach_agent_id, teach_content = _detect_teach_intent(instruction)
        if is_teach and teach_agent_id and teach_content:
            from skills.skill_web_research import teach_agent
            teach_agent(teach_agent_id, teach_content, source="COO/Emilie")
            return f"✅ Leçon injectée pour {teach_agent_id} : \"{teach_content[:100]}...\""

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
