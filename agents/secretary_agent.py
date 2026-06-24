"""Secretary Agent — Nadia Faure, Secrétaire de Direction ALNUA."""

from __future__ import annotations

import logging
from typing import Any

from agents.base import LLMClient, log_agent_action, parse_json_response
from database.supabase_client import SupabaseClient, get_supabase
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from config.agent_operating_spec import get_system_prompt
from skills.skill_langfuse import trace_agent

logger = logging.getLogger(__name__)


class SecretaryAgent:
    AGENT_NAME = "secretary"

    SYSTEM_PROMPT = get_system_prompt("secretary")

    def __init__(self, db: SupabaseClient | None = None, llm: LLMClient | None = None) -> None:
        self.db = db or get_supabase()
        self.llm = llm or LLMClient()

    # ------------------------------------------------------------------
    # Email
    # ------------------------------------------------------------------

    @trace_agent("secretary")
    def draft_email(
        self,
        subject: str,
        context: str,
        recipient: str,
        tone: str = "professionnel",
        language: str = "fr",
    ) -> dict[str, Any]:
        """Rédige un email professionnel."""
        prompt = inject_learning_context(
            f"""Rédige un email professionnel.
Destinataire : {recipient}
Objet : {subject}
Contexte / informations à inclure : {context}
Ton souhaité : {tone}
Langue : {language}

Réponds en JSON :
{{
  "subject": "Objet de l'email",
  "body": "Corps complet de l'email",
  "suggested_send_time": "matin|après-midi|urgent"
}}""",
            self.AGENT_NAME, subject,
        )
        raw = self.llm.complete(self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "draft_email",
            input_summary=f"À: {recipient} | Objet: {subject}",
            output_summary=result.get("subject", "Email rédigé"),
        )
        try:
            record_task_learning(self.AGENT_NAME, "draft_email", str(result), success=True)
        except Exception:
            pass
        return result

    @trace_agent("secretary")
    def triage_emails(self, emails: list[dict[str, str]]) -> dict[str, Any]:
        """Analyse et priorise une liste d'emails entrants."""
        emails_text = "\n\n".join(
            f"[{i+1}] De: {e.get('from','')} | Objet: {e.get('subject','')} | Corps: {e.get('body','')[:300]}"
            for i, e in enumerate(emails)
        )
        prompt = inject_learning_context(
            f"""Analyse ces emails entrants et classe-les par priorité.
{emails_text}

Réponds en JSON :
{{
  "urgent": [{{ "index": 1, "action": "string", "summary": "string" }}],
  "normal": [...],
  "low": [...],
  "spam_or_ignore": [...]
}}""",
            self.AGENT_NAME, "triage emails",
        )
        raw = self.llm.complete(self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME)
        return parse_json_response(raw)

    # ------------------------------------------------------------------
    # Contrats
    # ------------------------------------------------------------------

    @trace_agent("secretary")
    def draft_contract(
        self,
        contract_type: str,
        party_name: str,
        scope: str,
        duration: str,
        compensation: str = "",
        special_clauses: str = "",
    ) -> dict[str, Any]:
        """Rédige un contrat de collaboration.

        contract_type: 'partenariat' | 'prestation' | 'nda' | 'freelance'
        """
        prompt = inject_learning_context(
            f"""Rédige un contrat de {contract_type} professionnel entre ALNUA et {party_name}.

Périmètre / objet : {scope}
Durée : {duration}
Rémunération / contrepartie : {compensation or 'À définir'}
Clauses spéciales : {special_clauses or 'Aucune'}

Réponds en JSON :
{{
  "title": "Titre officiel du contrat",
  "preamble": "Préambule",
  "articles": [
    {{ "number": 1, "title": "Objet", "content": "..." }},
    {{ "number": 2, "title": "Durée", "content": "..." }},
    {{ "number": 3, "title": "Obligations des parties", "content": "..." }},
    {{ "number": 4, "title": "Rémunération", "content": "..." }},
    {{ "number": 5, "title": "Confidentialité", "content": "..." }},
    {{ "number": 6, "title": "Résiliation", "content": "..." }},
    {{ "number": 7, "title": "Droit applicable", "content": "..." }}
  ],
  "signature_block": "Bloc signature standard"
}}""",
            self.AGENT_NAME, f"contrat {contract_type} {party_name}",
        )
        raw = self.llm.complete(
            self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.3, max_tokens=6000
        )
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "draft_contract",
            input_summary=f"Type: {contract_type} | Partie: {party_name}",
            output_summary=result.get("title", "Contrat rédigé"),
        )
        return result

    # ------------------------------------------------------------------
    # Agenda & réunions
    # ------------------------------------------------------------------

    @trace_agent("secretary")
    def plan_meeting(
        self,
        participants: list[str],
        topic: str,
        duration_minutes: int = 60,
        constraints: str = "",
    ) -> dict[str, Any]:
        """Génère un plan de réunion structuré avec ordre du jour."""
        prompt = inject_learning_context(
            f"""Prépare une réunion pour l'équipe ALNUA.
Participants : {', '.join(participants)}
Sujet : {topic}
Durée : {duration_minutes} minutes
Contraintes / contexte : {constraints or 'Aucune'}

Réponds en JSON :
{{
  "title": "Titre de la réunion",
  "objective": "Objectif en une phrase",
  "agenda": [
    {{ "time": "00:00", "duration": 10, "item": "Ouverture", "presenter": "string" }}
  ],
  "prep_items": ["Ce que chaque participant doit préparer"],
  "expected_outcomes": ["Décision 1", "Livrable 2"]
}}""",
            self.AGENT_NAME, f"réunion {topic}",
        )
        raw = self.llm.complete(self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME)
        return parse_json_response(raw)

    @trace_agent("secretary")
    def write_meeting_notes(
        self,
        meeting_title: str,
        raw_notes: str,
        participants: list[str],
    ) -> dict[str, Any]:
        """Transforme des notes brutes en compte rendu structuré."""
        prompt = inject_learning_context(
            f"""Transforme ces notes brutes de réunion en compte rendu officiel.
Réunion : {meeting_title}
Participants : {', '.join(participants)}

Notes brutes :
{raw_notes}

Réponds en JSON :
{{
  "title": "Compte rendu — {meeting_title}",
  "date": "À renseigner",
  "participants": [...],
  "summary": "Résumé exécutif (3-5 phrases)",
  "decisions": ["Décision 1", "Décision 2"],
  "action_items": [
    {{ "action": "string", "owner": "string", "deadline": "string" }}
  ],
  "next_meeting": "string or null"
}}""",
            self.AGENT_NAME, meeting_title,
        )
        raw = self.llm.complete(self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "write_meeting_notes",
            input_summary=meeting_title,
            output_summary=f"{len(result.get('action_items', []))} actions items",
        )
        return result

    # ------------------------------------------------------------------
    # Natural language (Hub + Telegram)
    # ------------------------------------------------------------------

    @trace_agent("secretary")
    def handle_instruction(self, instruction: str, *, session_id: str = "hub") -> str:
        """
        Point d'entrée langage naturel pour Emilie — Telegram et Hub.
        session_id isolates pending email drafts (hub vs Telegram chat).
        """
        instruction = instruction.strip()
        if not instruction:
            return "Je suis là — dis-moi ce dont tu as besoin (ton mail, ton planning, contrat, rapport de nuit, Academy…)."

        from services.secretary_intents import (
            build_academy_status_brief,
            build_morning_brief_for_secretary,
            build_night_report,
            detect_academy_intent,
            detect_aria_delegation,
            detect_briefing,
            detect_calendar_intent,
            detect_connect_intent,
            detect_contract_intent,
            detect_email_intent,
            detect_inbox_intent,
            detect_meeting_intent,
            detect_night_report,
            detect_research_intent,
            detect_send_confirm,
            detect_wake_ops,
            extract_aria_delegation_message,
            extract_research_query,
            format_json_reply,
        )

        try:
            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "handle_instruction",
                input_summary=instruction[:120],
                output_summary="en cours",
                status="pending",
            )
        except Exception:
            pass

        if detect_send_confirm(instruction):
            return self._handle_send_confirm(session_id)

        if detect_connect_intent(instruction):
            return self._handle_connect_nl(instruction)

        if detect_inbox_intent(instruction):
            return self._handle_inbox_nl(instruction)

        if detect_calendar_intent(instruction):
            return self._handle_calendar_nl(instruction)

        if detect_night_report(instruction):
            report = build_night_report()
            self._finish_instruction(instruction, report)
            return report

        if detect_briefing(instruction):
            brief = build_morning_brief_for_secretary()
            self._finish_instruction(instruction, brief[:200])
            return brief

        if detect_wake_ops(instruction):
            return self._handle_wake_ops(instruction)

        if detect_research_intent(instruction):
            return self._handle_research(instruction, session_id=session_id)

        if detect_aria_delegation(instruction):
            return self._handle_aria_delegation(instruction)

        if detect_academy_intent(instruction):
            brief = build_academy_status_brief()
            self._finish_instruction(instruction, brief[:200])
            return brief

        if detect_email_intent(instruction):
            return self._handle_email_nl(instruction, session_id=session_id)

        if detect_contract_intent(instruction):
            return self._handle_contract_nl(instruction)

        if detect_meeting_intent(instruction):
            return self._handle_meeting_nl(instruction, session_id=session_id)

        tg_chat = session_id.removeprefix("tg:") if session_id.startswith("tg:") else None
        return self._handle_conversation(instruction, chat_id=tg_chat)

    def _finish_instruction(self, instruction: str, output: str) -> None:
        try:
            log_agent_action(
                self.db,
                self.AGENT_NAME,
                "handle_instruction",
                input_summary=instruction[:120],
                output_summary=output[:200],
                status="success",
            )
            record_task_learning(self.AGENT_NAME, "handle_instruction", output[:300], success=True)
        except Exception:
            pass

    def _handle_email_nl(self, instruction: str, *, session_id: str = "hub") -> str:
        prompt = inject_learning_context(
            f"""Emilie demande de rédiger un email. Extrais destinataire, objet et contexte de :
{instruction}

Réponds en JSON :
{{"recipient": "...", "subject": "...", "context": "...", "tone": "professionnel|chaleureux|formel"}}""",
            self.AGENT_NAME,
            instruction[:80],
        )
        raw = self.llm.complete(self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.3)
        meta = parse_json_response(raw)
        recipient = meta.get("recipient") or "À confirmer"
        draft = self.draft_email(
            subject=meta.get("subject") or "Sans objet",
            context=meta.get("context") or instruction,
            recipient=recipient,
            tone=meta.get("tone") or "professionnel",
        )
        from services.secretary_drafts import store_email_draft
        from services.secretary_intents import format_json_reply

        store_email_draft(
            session_id,
            to=recipient,
            subject=draft.get("subject", ""),
            body=draft.get("body", ""),
        )
        out = format_json_reply(draft, kind="email")
        out += (
            "\n\n📌 **Brouillon enregistré** — dis « envoie le mail » pour valider l'envoi Gmail, "
            "ou modifie ta demande."
        )
        self._finish_instruction(instruction, out)
        return out

    def _handle_send_confirm(self, session_id: str) -> str:
        from services.secretary_drafts import confirm_and_send

        result = confirm_and_send(session_id)
        msg = result.get("message", "Erreur")
        self._finish_instruction("confirm send", msg)
        return msg

    def _handle_connect_nl(self, instruction: str) -> str:
        from services.secretary_composio import (
            connection_status_text,
            get_oauth_link_for_ceo,
            is_connected,
        )

        lower = instruction.lower()
        if "calendrier" in lower or "calendar" in lower or "agenda" in lower:
            if is_connected("googlecalendar"):
                return "✅ Google Calendar est déjà connecté.\n\n" + connection_status_text()
            link = get_oauth_link_for_ceo("GOOGLECALENDAR")
            return f"📅 Connecte ton agenda :\n{link}\n\nOuvre le lien, autorise l'accès, puis réessaie."

        if is_connected("gmail"):
            gmail_line = "✅ Gmail déjà connecté."
        else:
            link = get_oauth_link_for_ceo("GMAIL")
            gmail_line = f"📧 Connecte Gmail :\n{link}"

        return f"{gmail_line}\n\n{connection_status_text()}"

    def _handle_inbox_nl(self, instruction: str) -> str:
        from services.secretary_composio import fetch_inbox_emails, is_connected

        if not is_connected("gmail"):
            return (
                "Gmail n'est pas encore connecté.\n"
                "Dis « connecte gmail » ou `/connect gmail` sur Telegram."
            )

        emails = fetch_inbox_emails(max_results=8)
        if not emails:
            return "Boîte INBOX vide ou lecture impossible pour l'instant."

        triage = self.triage_emails(emails)
        urgent = triage.get("urgent") or []
        normal = triage.get("normal") or []
        lines = [f"📬 **{len(emails)} derniers mails (INBOX)**", ""]
        if urgent:
            lines.append("🔴 **Urgent :**")
            for item in urgent[:4]:
                lines.append(f"• {item.get('summary', item)}")
            lines.append("")
        if normal:
            lines.append("📋 **À traiter :**")
            for item in normal[:5]:
                lines.append(f"• {item.get('summary', item)}")
        low = triage.get("low") or []
        if low:
            lines.append(f"\n_{len(low)} mail(s) priorité basse._")
        out = "\n".join(lines)
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_calendar_nl(self, instruction: str) -> str:
        from services.secretary_composio import (
            create_calendar_event,
            fetch_calendar_events,
            is_connected,
        )

        if not is_connected("googlecalendar"):
            return (
                "Google Calendar non connecté.\n"
                "Dis « connecte mon calendrier » ou `/connect googlecalendar`."
            )

        lower = instruction.lower()
        if any(k in lower for k in ("crée", "cree", "ajoute", "planifie", "réserve", "reserve")):
            return self._handle_meeting_nl(instruction, session_id="hub", push_calendar=True)

        events = fetch_calendar_events(days_ahead=3)
        if not events:
            return "Aucun événement trouvé sur les 3 prochains jours (ou lecture API en cours)."

        lines = ["📅 **Agenda (3 jours)**", ""]
        for ev in events[:10]:
            loc = f" — {ev['location']}" if ev.get("location") else ""
            lines.append(f"• {ev.get('when', '?')} — {ev.get('title', '?')}{loc}")
        out = "\n".join(lines)
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_contract_nl(self, instruction: str) -> str:
        prompt = inject_learning_context(
            f"""Extrais les infos contrat de la demande d'Emilie :
{instruction}

JSON : {{"contract_type": "nda|prestation|partenariat", "party_name": "...", "scope": "...", "duration": "..."}}""",
            self.AGENT_NAME,
            instruction[:80],
        )
        raw = self.llm.complete(self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.2)
        meta = parse_json_response(raw)
        draft = self.draft_contract(
            contract_type=meta.get("contract_type") or "prestation",
            party_name=meta.get("party_name") or "À confirmer",
            scope=meta.get("scope") or instruction,
            duration=meta.get("duration") or "À définir",
        )
        from services.secretary_intents import format_json_reply

        out = format_json_reply(draft, kind="contract")
        self._finish_instruction(instruction, out)
        return out

    def _handle_meeting_nl(
        self,
        instruction: str,
        *,
        session_id: str = "hub",
        push_calendar: bool = False,
    ) -> str:
        lower = instruction.lower()
        if any(k in lower for k in ("compte rendu", "cr de", "notes de")):
            plan = self.write_meeting_notes(
                meeting_title="Réunion",
                raw_notes=instruction,
                participants=["Emilie"],
            )
            from services.secretary_intents import format_json_reply

            out = format_json_reply(plan, kind="notes")
            self._finish_instruction(instruction, out)
            return out

        prompt = inject_learning_context(
            f"""Extrais participants, sujet, durée et date/heure si mentionnée de :
{instruction}

JSON : {{"participants": ["..."], "topic": "...", "duration_minutes": 60, "constraints": "", "start_datetime": "ISO8601 ou vide"}}""",
            self.AGENT_NAME,
            instruction[:80],
        )
        raw = self.llm.complete(self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.2)
        meta = parse_json_response(raw)
        plan = self.plan_meeting(
            participants=meta.get("participants") or ["Emilie"],
            topic=meta.get("topic") or instruction,
            duration_minutes=int(meta.get("duration_minutes") or 60),
            constraints=meta.get("constraints") or "",
        )
        from services.secretary_intents import format_json_reply

        out = format_json_reply(plan, kind="meeting")

        if push_calendar or meta.get("start_datetime"):
            from services.secretary_composio import create_calendar_event, is_connected

            if is_connected("googlecalendar") and meta.get("start_datetime"):
                created = create_calendar_event(
                    title=plan.get("title") or meta.get("topic") or "Réunion",
                    start_datetime=str(meta["start_datetime"]),
                    description=plan.get("objective") or "",
                    duration_minutes=int(meta.get("duration_minutes") or 60),
                )
                if created.get("success"):
                    out += "\n\n✅ Événement ajouté à Google Calendar."
                else:
                    out += f"\n\n⚠️ Calendar : {created.get('error', 'échec')}"
            elif push_calendar:
                out += "\n\n_Précise date/heure pour créer l'événement Calendar._"

        self._finish_instruction(instruction, out)
        return out

    @staticmethod
    def _telegram_chat_id(session_id: str) -> int | None:
        if not session_id.startswith("tg:"):
            return None
        try:
            return int(session_id.split(":", 1)[1])
        except (ValueError, IndexError):
            return None

    def _handle_research(self, instruction: str, *, session_id: str = "hub") -> str:
        from agents.coo_agent import _detect_research_intent, _extract_research_topic
        from services.bureau_library import generate_ceo_report, run_bureau_research
        from services.secretary_intents import extract_research_query

        chat_id = self._telegram_chat_id(session_id)
        is_telegram = chat_id is not None

        query = extract_research_query(instruction)
        if query == "__report__":
            report = generate_ceo_report(days=7)
            out = report.get("markdown") or report.get("executive_summary", "Rapport généré.")
            self._finish_instruction(instruction, out[:200])
            return out

        is_research, research_agent = _detect_research_intent(instruction)
        if is_research and research_agent == "rnd_agent":
            topic = _extract_research_topic(instruction, research_agent) or query
            if topic and len(topic) >= 4:
                from services.coo_telegram_intents import launch_rnd_investigation

                out = launch_rnd_investigation(topic, chat_id=chat_id)
                self._finish_instruction(instruction, out[:200])
                return out

        result = run_bureau_research(
            query,
            requested_by="nadia",
            blocking=not is_telegram,
            notify_chat_id=chat_id,
        )
        if not is_telegram and result.get("entries_saved") is not None:
            n = result.get("entries_saved", 0)
            out = (
                f"📚 **Recherche terminée** — « {query} »\n\n"
                f"**{n}** fiche(s) archivée(s) dans la bibliothèque.\n"
                "Rien n'a été supprimé — consulte **Bibliothèque** dans le Hub."
            )
        else:
            out = (
                f"📚 **Recherche lancée** — « {query} »\n\n"
                f"{result.get('message', '')}\n\n"
                + (
                    "Je t'enverrai le bilan ici dès que c'est prêt (~1-3 min)."
                    if is_telegram
                    else "Tout est archivé dans la bibliothèque. "
                    "Demande « rapport bibliothèque » pour un résumé CEO."
                )
            )
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_wake_ops(self, instruction: str) -> str:
        from services.agent_wake import wake_agents

        result = wake_agents(notify=False, retry_failed=True)
        summary = result.get("summary", "")
        out = (
            "✅ **Pipeline Academy relancé** — Théo (dev_app) reprend les exercices en file.\n\n"
            f"{summary}"
        )
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_aria_delegation(self, instruction: str) -> str:
        from agents.coo_agent import COOAgent
        from services.secretary_intents import extract_aria_delegation_message

        payload = extract_aria_delegation_message(instruction)
        try:
            response = COOAgent(self.db).handle_instruction(payload)
        except Exception:
            response = (
                "Aria est indisponible pour l'instant — vérifie que le bot COO tourne "
                "(@Alnua_coo_bot) ou que le Hub API est démarré."
            )
        out = f"📨 **Transmis à Aria** :\n\n{response}"
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_conversation(
        self,
        instruction: str,
        *,
        chat_id: int | str | None = None,
    ) -> str:
        from services.secretary_intents import build_academy_status_brief
        from services.telegram_chat_memory import get_context_block
        from services.telegram_presence import CANNOT_DO_NADIA, hub_online

        context = build_academy_status_brief()
        history = get_context_block(chat_id)
        hub_line = "Hub en ligne." if hub_online() else "Hub ARRÊTÉ — pas de pipeline ni actions lourdes."

        prompt = inject_learning_context(
            f"""Emilie t'écrit en langage naturel :
{instruction}

{history}

Contexte ALNUA :
{context}
État technique : {hub_line}

Réponds comme Nadia Faure, secrétaire personnelle d'Emilie (CEO) chez ALNUA.
Français, professionnel et chaleureux, 3 à 8 phrases max.
Tu tutoies Emilie. C'est SON agenda, SES mails.

Si la demande est hors de ton périmètre (ops lourdes, R&D, pipeline) :
dis-le clairement et propose de transmettre à Aria ou une alternative concrète.
Si tu ne comprends pas : demande une précision au lieu de rester vague.
Pas de JSON — texte direct.""",
            self.AGENT_NAME,
            instruction[:80],
        )
        try:
            raw = self.llm.complete(
                self.SYSTEM_PROMPT, prompt, agent_id=self.AGENT_NAME, temperature=0.5
            )
            text = (raw or "").strip()
            if not text:
                text = CANNOT_DO_NADIA
        except Exception as exc:
            logger.warning("secretary conversation failed: %s", exc)
            text = (
                "Je n'ai pas pu formuler une réponse (connexion IA ou Hub).\n\n"
                + CANNOT_DO_NADIA
            )
        self._finish_instruction(instruction, text)
        return text
