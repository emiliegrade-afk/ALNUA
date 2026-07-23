"""Pending email drafts awaiting CEO confirmation before Gmail send."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass
class EmailDraft:
    to: str
    subject: str
    body: str
    created_at: str

    def to_dict(self) -> dict[str, str]:
        return {
            "to": self.to,
            "subject": self.subject,
            "body": self.body,
            "created_at": self.created_at,
        }


_pending: dict[str, EmailDraft] = {}


def store_email_draft(session_id: str, *, to: str, subject: str, body: str) -> None:
    _pending[session_id] = EmailDraft(
        to=to.strip(),
        subject=subject.strip(),
        body=body.strip(),
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def get_email_draft(session_id: str) -> EmailDraft | None:
    return _pending.get(session_id)


def clear_email_draft(session_id: str) -> None:
    _pending.pop(session_id, None)


def confirm_and_send(session_id: str) -> dict[str, Any]:
    """Send pending draft via Composio Gmail. Returns {success, message}."""
    draft = get_email_draft(session_id)
    if not draft:
        return {
            "success": False,
            "message": "Aucun brouillon en attente. Demande-moi de rédiger un mail d'abord.",
        }
    if not draft.to or "@" not in draft.to:
        return {
            "success": False,
            "message": f"Destinataire invalide : {draft.to!r}. Précise l'adresse email.",
        }

    from services.secretary_composio import send_email

    result = send_email(draft.to, draft.subject, draft.body)
    if result.get("success"):
        clear_email_draft(session_id)
        return {
            "success": True,
            "message": f"✅ Mail envoyé à {draft.to}\nObjet : {draft.subject}",
        }
    return {
        "success": False,
        "message": f"Échec envoi : {result.get('error', 'erreur inconnue')}",
    }
