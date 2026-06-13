"""CrewAI tools that call the ALNUA Hub FastAPI (real HTTP, not simulated text)."""

from __future__ import annotations

import os

import requests
from crewai.tools import tool

from config.settings import get_settings

BASE_URL = os.getenv(
    "HUB_API_URL",
    f"http://localhost:{get_settings().api_port}",
)


def _hub_headers() -> dict[str, str]:
    return {"X-Hub-Key": get_settings().hub_api_key}


def _api_json(method: str, path: str, **kwargs: object) -> str:
    """Execute an HTTP call and return JSON text or an error message."""
    url = f"{BASE_URL.rstrip('/')}{path}"
    headers = dict(kwargs.pop("headers", {}) or {})
    headers.update(_hub_headers())
    try:
        response = requests.request(
            method, url, timeout=30, headers=headers, **kwargs
        )
        response.raise_for_status()
        return str(response.json())
    except requests.RequestException as exc:
        body = ""
        if exc.response is not None:
            try:
                body = str(exc.response.json())
            except Exception:
                body = exc.response.text[:500]
        return f"API error ({method} {path}): {exc} {body}".strip()


@tool("Créer un ticket")
def create_ticket(
    project_id: str,
    title: str,
    type: str,
    priority: str,
    description: str,
) -> str:
    """Crée un ticket dans le Hub ALNUA via l'API."""
    return _api_json(
        "POST",
        "/tickets",
        json={
            "project_id": project_id,
            "title": title,
            "type": type,
            "priority": priority,
            "description": description,
            "source": "qa_agent",
        },
    )


@tool("Lister les projets")
def list_projects() -> str:
    """Retourne la liste des projets ALNUA avec leurs IDs."""
    return _api_json("GET", "/projects")


@tool("Créer un item roadmap")
def create_roadmap_item(
    project_id: str,
    title: str,
    priority: str,
    description: str,
) -> str:
    """Crée un item dans la roadmap."""
    return _api_json(
        "POST",
        "/roadmap",
        json={
            "project_id": project_id,
            "title": title,
            "priority": priority,
            "description": description,
            "status": "planned",
        },
    )


@tool("Lister les tickets")
def list_tickets(project_id: str = "", status: str = "") -> str:
    """Liste les tickets du Hub. Filtres optionnels : project_id, status (open/in_progress/done)."""
    params: dict[str, str] = {}
    if project_id:
        params["project_id"] = project_id
    if status:
        params["status"] = status
    return _api_json("GET", "/tickets", params=params)


@tool("Mettre à jour un ticket")
def update_ticket(ticket_id: str, status: str = "", priority: str = "") -> str:
    """Met à jour le status ou la priorité d'un ticket existant."""
    payload: dict[str, str] = {}
    if status:
        payload["status"] = status
    if priority:
        payload["priority"] = priority
    return _api_json("PATCH", f"/tickets/{ticket_id}", json=payload)


@tool("Générer prompt Cursor pour un ticket")
def generate_cursor_prompt(ticket_id: str) -> str:
    """Demande au Spec Agent de générer un prompt Cursor prêt à coller pour ce ticket."""
    return _api_json("POST", f"/tickets/{ticket_id}/generate-cursor-prompt")


@tool("Lister la roadmap")
def list_roadmap(project_id: str = "", status: str = "") -> str:
    """Liste les items de la roadmap. Filtres optionnels : project_id, status."""
    params: dict[str, str] = {}
    if project_id:
        params["project_id"] = project_id
    if status:
        params["status"] = status
    return _api_json("GET", "/roadmap", params=params)


@tool("Générer des posts réseaux sociaux")
def generate_posts(
    project_id: str,
    dev_log: str,
    platforms: str = "instagram,tiktok,x",
) -> str:
    """Génère des posts réseaux sociaux depuis une note de dev log."""
    return _api_json(
        "POST",
        "/agents/content/generate",
        json={
            "project_id": project_id,
            "dev_log": dev_log,
            "content_types": ["post"],
            "platforms": [p.strip() for p in platforms.split(",") if p.strip()],
        },
    )


@tool("Lister les posts en attente")
def list_pending_posts(project_id: str = "") -> str:
    """Liste les posts en attente d'approbation."""
    params: dict[str, str] = {"status": "pending_approval"}
    if project_id:
        params["project_id"] = project_id
    return _api_json("GET", "/posts", params=params)


@tool("Créer une entrée dev log")
def create_dev_log(project_id: str, content: str) -> str:
    """Enregistre une note de développement pour un projet."""
    return _api_json(
        "POST",
        "/dev-log",
        json={"project_id": project_id, "content": content},
    )


@tool("Résumé analytics")
def get_analytics_summary(project_id: str = "") -> str:
    """Retourne le résumé KPI du mois (downloads, MRR, churn...)."""
    params: dict[str, str] = {}
    if project_id:
        params["project_id"] = project_id
    return _api_json("GET", "/analytics/summary", params=params)


@tool("Rapport du jour")
def get_daily_briefing() -> str:
    """Retourne le briefing quotidien ALNUA — tickets urgents, posts en attente, roadmap imminente."""
    return _api_json("GET", "/briefing/today")


@tool("Capture rapide")
def quick_capture(type: str, content: str, project_id: str, priority: str = "medium") -> str:
    """Capture rapide : envoie une idée, bug, item roadmap ou note. type = ticket|idea|roadmap|note"""
    return _api_json(
        "POST",
        "/quick-capture",
        json={
            "type": type,
            "content": content,
            "project_id": project_id,
            "priority": priority,
        },
    )


HUB_TOOLS = [
    create_ticket,
    list_projects,
    create_roadmap_item,
    list_tickets,
    update_ticket,
    generate_cursor_prompt,
    list_roadmap,
    generate_posts,
    list_pending_posts,
    create_dev_log,
    get_analytics_summary,
    get_daily_briefing,
    quick_capture,
]

PM_TOOLS = [
    list_tickets,
    update_ticket,
    list_roadmap,
    create_ticket,
    create_roadmap_item,
]

QA_TOOLS = [create_ticket, list_tickets, update_ticket]

CONTENT_TOOLS = [generate_posts, list_pending_posts, create_dev_log]

SPEC_TOOLS = [list_tickets, generate_cursor_prompt]
