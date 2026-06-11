"""Spec Agent — generates Cursor-ready prompts from tickets."""

from __future__ import annotations

from typing import Any

from crewai import Agent, LLM

from agents.base import LLMClient, log_agent_action
from agents.tools.hub_tools import SPEC_TOOLS
from database.supabase_client import SupabaseClient, get_supabase


class SpecAgent:
    AGENT_NAME = "spec_agent"

    SYSTEM_PROMPT = """Tu es l'agent Spec d'ALNUA. Tu transformes des tickets en prompts
précis pour Cursor (Composer) afin qu'Emilie (solo dev) implémente le fix ou la feature.

Structure OBLIGATOIRE du prompt (en français, markdown) :

Ouvre `[fichier probable le plus pertinent]`.

Le problème est : [description claire du bug ou du besoin en 2-4 phrases].

Voici ce qu'il faut faire :
1. [étape concrète]
2. [étape concrète]
3. [étape concrète]
(ajoute des étapes si nécessaire)

Fichiers concernés :
- `[chemin/relatif/fichier.ext]`
- `[autre fichier si pertinent]`

Teste avec :
```bash
[commande de test ou vérification manuelle]
```

Critères d'acceptation :
- [ ] [critère mesurable]
- [ ] [critère mesurable]

Sois spécifique au stack ALNUA (Python FastAPI backend, Next.js 14 frontend, Supabase).
Ne mets pas de blabla — uniquement du contenu actionnable prêt à coller dans Cursor."""

    def __init__(self, db: SupabaseClient | None = None, llm: LLMClient | None = None) -> None:
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()
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
            temperature=0.25,
        )

    def _ensure_crew_agent(self) -> Agent:
        if self._crew_agent is None:
            self._crew_llm = self._build_crew_llm()
            self._crew_agent = Agent(
                role="Spec ALNUA",
                goal="Générer des prompts Cursor depuis les tickets via l'API Hub",
                backstory=self.SYSTEM_PROMPT,
                tools=SPEC_TOOLS,
                llm=self._crew_llm,
                allow_delegation=False,
                max_iter=8,
            )
        return self._crew_agent

    def generate_cursor_prompt(self, ticket_id: str) -> dict[str, Any]:
        tickets = self.db.select("tickets", filters={"id": ticket_id})
        if not tickets:
            raise ValueError(f"Ticket {ticket_id} not found")

        ticket = tickets[0]
        project = self.db.select("projects", filters={"id": ticket["project_id"]})
        project_info = project[0] if project else {}

        return self._generate_and_save(ticket, project_info)

    def generate_from_ticket(
        self,
        ticket: dict[str, Any],
        project_info: dict[str, Any] | None = None,
    ) -> str:
        """Génère un prompt Cursor à partir d'un ticket complet (sans sauvegarde)."""
        project_info = project_info or {}
        user_prompt = self._build_user_prompt(ticket, project_info)
        return self.llm.complete(
            self.SYSTEM_PROMPT,
            user_prompt,
            temperature=0.25,
            max_tokens=8192,
        )

    @staticmethod
    def _build_user_prompt(ticket: dict[str, Any], project_info: dict[str, Any]) -> str:
        return f"""Projet : {project_info.get('name', 'Unknown')} — branche {project_info.get('branch', '')}
Description projet : {project_info.get('description', '')}

Ticket :
- Type : {ticket.get('type', '')}
- Priorité : {ticket.get('priority', '')}
- Titre : {ticket.get('title', '')}
- Description : {ticket.get('description', '')}
- Source : {ticket.get('source', '')}

Génère le prompt Cursor complet en suivant EXACTEMENT la structure demandée."""

    def _generate_and_save(
        self,
        ticket: dict[str, Any],
        project_info: dict[str, Any],
    ) -> dict[str, Any]:
        ticket_id = ticket["id"]
        user_prompt = self._build_user_prompt(ticket, project_info)

        try:
            cursor_prompt = self.llm.complete(
                self.SYSTEM_PROMPT,
                user_prompt,
                temperature=0.25,
                max_tokens=8192,
            )
            updates: dict[str, Any] = {"cursor_prompt": cursor_prompt}
            if ticket.get("status") == "open":
                updates["status"] = "in_progress"

            updated = self.db.update("tickets", ticket_id, updates)
            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "generate_cursor_prompt",
                input_summary=ticket.get("title", "")[:200],
                output_summary=f"{len(cursor_prompt)} chars",
                status="success",
                project_id=ticket.get("project_id"),
            )
            return updated
        except Exception as exc:
            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "generate_cursor_prompt",
                input_summary=ticket.get("title", "")[:200],
                output_summary=str(exc),
                status="error",
                project_id=ticket.get("project_id"),
            )
            raise

    def batch_generate_for_open_tickets(self, project_id: str) -> list[dict[str, Any]]:
        tickets = self.db.select(
            "tickets",
            filters={"project_id": project_id, "status": "open"},
            limit=10,
        )
        results = []
        for ticket in tickets:
            if not ticket.get("cursor_prompt"):
                project = self.db.select("projects", filters={"id": project_id})
                project_info = project[0] if project else {}
                results.append(self._generate_and_save(ticket, project_info))
        return results
