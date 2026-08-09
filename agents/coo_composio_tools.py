"""COO Composio / CrewAI module tools — extracted from coo_agent (Vague 2 / BUG-004)."""

from __future__ import annotations

from typing import Any

from crewai.tools import tool

from skills.skill_chroma import search_knowledge as _search
from skills.skill_composio import composio_execute, get_oauth_link


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
