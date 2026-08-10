"""Secretary agent — comms NL handlers (email, inbox, calendar, contract, meeting)."""
from __future__ import annotations

from agents.base import parse_json_response
from skills.skill_agent_learning import inject_learning_context


class SecretaryHandlersCommsMixin:
    """Requires ``SecretaryDocumentsMixin`` methods and ``AgentBase``."""

    def _handle_email_nl(self, instruction: str, *, session_id: str = "hub") -> str:
        prompt = inject_learning_context(
            f"""Emilie demande de rédiger un email. Extrais destinataire, objet et contexte de :
{instruction}

Réponds en JSON :
{{"recipient": "...", "subject": "...", "context": "...", "tone": "professionnel|chaleureux|formel"}}""",
            self.AGENT_NAME,
            instruction[:80],
        )
        raw = self._complete(prompt, temperature=0.3)
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
        raw = self._complete(prompt, temperature=0.2)
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
        raw = self._complete(prompt, temperature=0.2)
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
