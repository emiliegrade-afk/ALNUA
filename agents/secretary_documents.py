"""Secretary agent — document drafting (email, contract, meeting)."""
from __future__ import annotations

from typing import Any

from agents.base import log_agent_action, parse_json_response
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from skills.skill_langfuse import trace_agent


class SecretaryDocumentsMixin:
    """Requires ``self.AGENT_NAME``, ``self.db``, ``self._complete`` from ``AgentBase``."""

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
        raw = self._complete(prompt)
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
        raw = self._complete(prompt)
        return parse_json_response(raw)

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
        """Rédige un contrat de collaboration à partir du catalogue templates.

        contract_type: nda|partenariat|influenceur|pub|prestation|affiliation|freelance
        """
        from config.contract_templates_registry import template_prompt_block

        scaffold = template_prompt_block(contract_type)
        prompt = inject_learning_context(
            f"""Rédige un contrat professionnel entre ALNUA et {party_name}.
Type demandé : {contract_type}

{scaffold}

Périmètre / objet : {scope}
Durée : {duration}
Rémunération / contrepartie : {compensation or 'À définir'}
Clauses spéciales : {special_clauses or 'Aucune'}

Réponds en JSON :
{{
  "title": "Titre officiel du contrat",
  "template_id": "{contract_type}",
  "preamble": "Préambule",
  "articles": [
    {{ "number": 1, "title": "Objet", "content": "..." }}
  ],
  "signature_block": "Bloc signature standard",
  "needs_legal_review": true,
  "note": "Brouillon Nadia — à faire relire par Solène (legal_counsel) avant signature"
}}""",
            self.AGENT_NAME, f"contrat {contract_type} {party_name}",
        )
        raw = self._complete(prompt, temperature=0.3, max_tokens=6000)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "draft_contract",
            input_summary=f"Type: {contract_type} | Partie: {party_name}",
            output_summary=result.get("title", "Contrat rédigé"),
        )
        return result

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
        raw = self._complete(prompt)
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
        raw = self._complete(prompt)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "write_meeting_notes",
            input_summary=meeting_title,
            output_summary=f"{len(result.get('action_items', []))} actions items",
        )
        return result
