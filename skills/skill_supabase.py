"""CrewAI tools for reading ALNUA Hub data from Supabase REST API."""

from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request

from crewai.tools import tool

from config.settings import get_settings


def _supabase_credentials() -> tuple[str, str]:
    settings = get_settings()
    return settings.supabase_url, settings.supabase_key


def _sb_get(endpoint: str) -> list:
    supabase_url, supabase_key = _supabase_credentials()
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL / SUPABASE_KEY manquantes dans .env")
    req = urllib.request.Request(
        f"{supabase_url}/rest/v1/{endpoint}",
        headers={
            "apikey": supabase_key,
            "Authorization": f"Bearer {supabase_key}",
        },
    )
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


@tool("fetch_project_summary")
def fetch_project_summary(project_name: str) -> str:
    """Retourne un résumé d'un projet ALNUA : statut, tickets ouverts, dernière activité."""
    try:
        encoded = urllib.parse.quote(project_name)
        projects = _sb_get(f"projects?name=ilike.*{encoded}*&select=*")
        if not projects:
            return f"Projet '{project_name}' introuvable."
        p = projects[0]
        tickets = _sb_get(
            f"tickets?project_id=eq.{p['id']}&status=eq.open&select=id,title,priority"
        )
        return (
            f"Projet : {p['name']} ({p['branch']}) — statut : {p['status']}\n"
            f"Tickets ouverts : {len(tickets)}\n"
            + "\n".join(f"  - [{t['priority']}] {t['title']}" for t in tickets[:5])
        )
    except Exception as exc:
        return f"Erreur Supabase : {exc}"


@tool("list_all_projects")
def list_all_projects() -> str:
    """Liste tous les projets ALNUA actifs."""
    try:
        projects = _sb_get("projects?select=name,branch,status&order=created_at.desc")
        return "\n".join(
            f"- {p['name']} ({p['branch']}) — {p['status']}" for p in projects
        )
    except Exception as exc:
        return f"Erreur Supabase : {exc}"


@tool("get_llm_costs")
def get_llm_costs() -> str:
    """Retourne les coûts LLM des 7 derniers jours."""
    try:
        costs = _sb_get("llm_costs?select=*&order=created_at.desc&limit=20")
        total = sum(float(c.get("cost_usd", 0)) for c in costs)
        return (
            f"Coûts LLM (récents) : ${total:.4f}\n"
            f"Détail : {json.dumps(costs[:5], default=str)}"
        )
    except Exception as exc:
        return f"Erreur Supabase : {exc}"
