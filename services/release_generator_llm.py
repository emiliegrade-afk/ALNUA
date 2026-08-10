"""Release notes — OpenRouter LLM generation."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

import httpx
from fastapi import HTTPException

from agents.base import parse_json_response
from config.settings import get_settings

logger = logging.getLogger(__name__)

RELEASE_MODEL = "anthropic/claude-3-5-sonnet"

SYSTEM_PROMPT = (
    "Tu es un expert en communication produit pour apps mobiles. "
    "Tu transformes des notes techniques en release notes claires et attrayantes. "
    "Tes textes sont positifs, orientés bénéfice utilisateur, sans jargon technique."
)

USER_PROMPT_TEMPLATE = """Voici les entrées de dev log pour la version {version} du projet {project_name} :
{dev_log_entries}

Génère 3 versions :

1. APP STORE (max 4000 caractères) :
- Titre accrocheur
- Liste des nouveautés (bénéfices utilisateur, pas détails techniques)
- Corrections de bugs (regroupées, pas de détails techniques)
- Ton : professionnel et enthousiaste

2. GOOGLE PLAY (max 500 caractères) :
- Version ultra-condensée
- Seulement les 3-4 points les plus importants

3. CHANGELOG (format Keep a Changelog) :
## [{version}] - [{release_date}]
### Ajouté
### Modifié
### Corrigé
(en français, ton technique OK ici)

Réponds en JSON : {{ "app_store": "...", "google_play": "...", "changelog": "..." }}"""


def format_dev_log_entries(entries: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for entry in entries:
        log_date = entry.get("date", "")
        content = (entry.get("content") or "").strip()
        lines.append(f"- [{log_date}] {content}")
    return "\n".join(lines) if lines else "(aucune entrée dev_log)"


def call_openrouter(
    project_name: str,
    version: str,
    dev_log_entries: list[dict[str, Any]],
) -> dict[str, str]:
    settings = get_settings()
    if not settings.openrouter_api_key.strip():
        raise HTTPException(
            status_code=503,
            detail="OPENROUTER_API_KEY manquante — impossible de générer les release notes.",
        )

    release_date = date.today().isoformat()
    user_content = USER_PROMPT_TEMPLATE.format(
        version=version,
        project_name=project_name,
        dev_log_entries=format_dev_log_entries(dev_log_entries),
        release_date=release_date,
    )

    payload = {
        "model": RELEASE_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.5,
        "max_tokens": 4096,
    }
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://alnua-hub.local",
        "X-Title": "ALNUA Hub Release Notes",
    }

    try:
        with httpx.Client(timeout=120.0) as client:
            response = client.post(
                f"{settings.openrouter_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        raw = data["choices"][0]["message"]["content"]
        parsed = parse_json_response(raw)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("OpenRouter release notes generation failed")
        raise HTTPException(
            status_code=502,
            detail=f"Erreur génération LLM : {exc}",
        ) from exc

    app_store = str(parsed.get("app_store", "")).strip()
    google_play = str(parsed.get("google_play", "")).strip()
    changelog = str(parsed.get("changelog", "")).strip()

    if not app_store and not google_play and not changelog:
        raise HTTPException(
            status_code=502,
            detail="Réponse LLM invalide — JSON vide ou mal formé.",
        )

    return {
        "app_store": app_store[:4000],
        "google_play": google_play[:500],
        "changelog": changelog,
    }
