"""Spec Agent — generates Cursor-ready prompts from tickets."""

from __future__ import annotations

from typing import Any

from crewai import Agent, LLM

from agents.base import LLMClient, log_agent_action
from agents.tools.hub_tools import SPEC_TOOLS
from config.agent_personas import persona_prompt_intro
from database.supabase_client import SupabaseClient, get_supabase
from skills.skill_langfuse import trace_agent


class SpecAgent:
    AGENT_NAME = "spec_agent"

    SYSTEM_PROMPT = persona_prompt_intro("spec", role="Spec Rédacteur") + """. Tu transformes des tickets en prompts
precis pour Cursor (Composer) afin qu'Emilie (solo dev) implemente le fix ou la feature.

Structure OBLIGATOIRE du prompt (en francais, markdown) :

Ouvre `[fichier probable le plus pertinent]`.

Le probleme est : [description claire du bug ou du besoin en 2-4 phrases].

Voici ce qu'il faut faire :
1. [etape concrete]
2. [etape concrete]
3. [etape concrete]
(ajoute des etapes si necessaire)

Fichiers concernes :
- `[chemin/relatif/fichier.ext]`
- `[autre fichier si pertinent]`

Teste avec :
```bash
[commande de test ou verification manuelle]
```

Criteres d'acceptation :
- [ ] [critere mesurable]
- [ ] [critere mesurable]

Sois specifique au stack ALNUA (Python FastAPI backend, Next.js 14 frontend, Supabase).
Ne mets pas de blabla — uniquement du contenu actionnable pret a coller dans Cursor."""

    def __init__(self, db: SupabaseClient | None = None, llm: LLMClient | None = None) -> None:
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()
        self._crew_llm: LLM | None = None
        self._crew_agent: Agent | None = None

    def _build_crew_llm(self) -> LLM:
        from agents.base import build_crewai_llm
        return build_crewai_llm("spec", temperature=0.25)

    def _ensure_crew_agent(self) -> Agent:
        if self._crew_agent is None:
            self._crew_llm = self._build_crew_llm()
            self._crew_agent = Agent(
                role="Spec ALNUA",
                goal="Generer des prompts Cursor depuis les tickets via l'API Hub",
                backstory=self.SYSTEM_PROMPT,
                tools=SPEC_TOOLS,
                llm=self._crew_llm,
                allow_delegation=False,
                max_iter=8,
            )
        return self._crew_agent

    @trace_agent("spec_agent")
    def generate_cursor_prompt(self, ticket_id: str) -> dict[str, Any]:
        tickets = self.db.select("tickets", filters={"id": ticket_id})
        if not tickets:
            raise ValueError(f"Ticket {ticket_id} not found")
        ticket = tickets[0]
        project = self.db.select("projects", filters={"id": ticket["project_id"]})
        project_info = project[0] if project else {}
        return self._generate_and_save(ticket, project_info)

    @trace_agent("spec_agent")
    def generate_engineering_spec(
        self,
        dossier_id: str,
        *,
        force: bool = False,
        debate_rounds: int = 1,
    ) -> dict[str, Any]:
        """CEO package §10 — Product Engineering Spec."""
        from services.prd_engineering import run_engineering_spec_generation

        return run_engineering_spec_generation(
            dossier_id,
            force=force,
            debate_rounds=debate_rounds,
        )

    def generate_from_ticket(
        self,
        ticket: dict[str, Any],
        project_info: dict[str, Any] | None = None,
    ) -> str:
        """Genere un prompt Cursor a partir d'un ticket complet (sans sauvegarde)."""
        project_info = project_info or {}
        user_prompt = self._build_user_prompt(ticket, project_info)
        from skills.skill_agent_learning import inject_learning_context
        user_prompt = inject_learning_context(
            user_prompt, "spec", ticket.get("title", "") or "cursor prompt"
        )
        return self.llm.complete(
            self.SYSTEM_PROMPT,
            user_prompt,
            agent_id="spec",
            temperature=0.25,
            max_tokens=8192,
        )

    @trace_agent("spec_agent")
    def generate_and_write_dispatch(
        self,
        ticket: dict[str, Any],
        project_info: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Genere un prompt Cursor, l'ecrit sur disque et sauvegarde dans Supabase.

        Utilise par rnd_dispatch_executor (Phase 9 — Option A workspace).
        Retourne {cursor_prompt, file_path, slug, ticket_id}.

        Convention disque : ALNUA/{pole}/{slug}/{filename}
        -> direction/{slug}/spec-cursor-prompt.md
        """
        project_info = project_info or {}
        slug = project_info.get("slug") or ticket.get("workspace_slug") or ""

        cursor_prompt = self.generate_from_ticket(ticket, project_info)

        written_path: str | None = None
        if slug:
            try:
                from services.rnd_workspace import write_deliverable
                # Option A : pole=direction, slug=slug
                path = write_deliverable("direction", slug, "spec-cursor-prompt.md", cursor_prompt)
                written_path = str(path)
            except Exception as exc:
                import logging as _logging
                _logging.getLogger(__name__).warning(
                    "spec write_deliverable failed for slug=%s: %s", slug, exc
                )

        # Sauvegarde cursor_prompt dans le ticket Supabase si le ticket a un id
        ticket_id = ticket.get("id")
        if ticket_id:
            try:
                updates: dict[str, Any] = {"cursor_prompt": cursor_prompt}
                if ticket.get("status") == "open":
                    updates["status"] = "in_progress"
                self.db.update("tickets", ticket_id, updates)
            except Exception as exc:
                import logging as _logging
                _logging.getLogger(__name__).warning(
                    "spec ticket update failed for id=%s: %s", ticket_id, exc
                )

        log_agent_action(
            self.db,
            self.AGENT_NAME,
            "generate_and_write_dispatch",
            input_summary=ticket.get("title", "")[:200],
            output_summary=f"{len(cursor_prompt)} chars — path={written_path}",
        )

        return {
            "cursor_prompt": cursor_prompt,
            "file_path": written_path,
            "slug": slug,
            "ticket_id": ticket_id,
        }

    @staticmethod
    def _build_user_prompt(ticket: dict[str, Any], project_info: dict[str, Any]) -> str:
        return f"""Projet : {project_info.get('name', 'Unknown')} — branche {project_info.get('branch', '')}
Description projet : {project_info.get('description', '')}

Ticket :
- Type : {ticket.get('type', '')}
- Priorite : {ticket.get('priority', '')}
- Titre : {ticket.get('title', '')}
- Description : {ticket.get('description', '')}
- Source : {ticket.get('source', '')}

Genere le prompt Cursor complet en suivant EXACTEMENT la structure demandee."""

    def _generate_and_save(
        self,
        ticket: dict[str, Any],
        project_info: dict[str, Any],
    ) -> dict[str, Any]:
        ticket_id = ticket["id"]
        from skills.skill_agent_learning import inject_learning_context, record_task_learning

        user_prompt = self._build_user_prompt(ticket, project_info)
        user_prompt = inject_learning_context(
            user_prompt, "spec", ticket.get("title", "") or str(ticket_id)
        )

        try:
            cursor_prompt = self.llm.complete(
                self.SYSTEM_PROMPT,
                user_prompt,
                agent_id="spec",
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
            try:
                record_task_learning(
                    agent_id="spec",
                    task=f"generate cursor prompt {ticket_id}",
                    outcome=str(updated),
                    success=True,
                )
            except Exception:
                pass
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
