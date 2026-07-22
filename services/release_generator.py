"""Release notes generator — dev_log entries → App Store / Google Play / CHANGELOG."""

from __future__ import annotations

import json
import logging
from datetime import date, datetime
from pathlib import Path
from typing import Any

import httpx
from fastapi import HTTPException

from agents.base import parse_json_response
from agents.brainstorm_agent import BrainstormAgent
from config.settings import get_settings
from database.supabase_client import SupabaseClient, get_supabase
from services.brand_storage import BRAND_KITS_ROOT

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


def _format_dev_log_entries(entries: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for entry in entries:
        log_date = entry.get("date", "")
        content = (entry.get("content") or "").strip()
        lines.append(f"- [{log_date}] {content}")
    return "\n".join(lines) if lines else "(aucune entrée dev_log)"


def _is_missing_table_error(exc: Exception, table_name: str) -> bool:
    msg = str(exc)
    return table_name in msg and ("PGRST205" in msg or "schema cache" in msg)


def _get_last_release(db: SupabaseClient, project_id: str) -> dict[str, Any] | None:
    try:
        rows = (
            db.table("releases")
            .select("*")
            .eq("project_id", project_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
    except Exception as exc:
        if _is_missing_table_error(exc, "releases"):
            logger.warning("releases table missing — treating as no prior release")
            return None
        raise
    data = rows.data or []
    return data[0] if data else None


def _since_date_from_last_release(last_release: dict[str, Any]) -> date:
    release_date = last_release.get("release_date")
    if release_date:
        if isinstance(release_date, str):
            return date.fromisoformat(release_date[:10])
        return release_date
    created_at = last_release.get("created_at", "")
    if isinstance(created_at, str):
        return date.fromisoformat(created_at[:10])
    if isinstance(created_at, datetime):
        return created_at.date()
    return date.today()


def collect_dev_log_entries(
    db: SupabaseClient,
    project_id: str,
    *,
    since_date: date | None = None,
    dev_log_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """Load dev_log rows according to selection mode."""
    try:
        if dev_log_ids:
            response = (
                db.table("dev_log")
                .select("*")
                .eq("project_id", project_id)
                .in_("id", dev_log_ids)
                .order("date", desc=False)
                .execute()
            )
            return response.data or []

        if since_date is None:
            last_release = _get_last_release(db, project_id)
            if last_release:
                since_date = _since_date_from_last_release(last_release)
                # Strictly after last release day to avoid duplicating prior entries
                response = (
                    db.table("dev_log")
                    .select("*")
                    .eq("project_id", project_id)
                    .gt("date", since_date.isoformat())
                    .order("date", desc=False)
                    .execute()
                )
                return response.data or []
            since_date = date(1970, 1, 1)

        response = (
            db.table("dev_log")
            .select("*")
            .eq("project_id", project_id)
            .gte("date", since_date.isoformat())
            .order("date", desc=False)
            .execute()
        )
        return response.data or []
    except Exception as exc:
        if _is_missing_table_error(exc, "dev_log"):
            logger.warning("dev_log table missing — no entries to generate release notes from")
            return []
        raise


def _call_openrouter(
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
        dev_log_entries=_format_dev_log_entries(dev_log_entries),
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


def _write_changelog_file(project_slug: str, changelog_md: str) -> Path:
    """Write or prepend CHANGELOG.md in the project's brand_kits folder."""
    project_dir = BRAND_KITS_ROOT / project_slug
    project_dir.mkdir(parents=True, exist_ok=True)
    changelog_path = project_dir / "CHANGELOG.md"

    header = "# Changelog\n\n"
    if changelog_path.is_file():
        existing = changelog_path.read_text(encoding="utf-8")
        if existing.startswith("# Changelog"):
            body = existing[len("# Changelog") :].lstrip("\n")
            content = f"{header}{changelog_md.rstrip()}\n\n{body}".rstrip() + "\n"
        else:
            content = f"{header}{changelog_md.rstrip()}\n\n{existing}".rstrip() + "\n"
    else:
        content = f"{header}{changelog_md.rstrip()}\n"

    changelog_path.write_text(content, encoding="utf-8")
    return changelog_path


def generate_release_notes(
    project_id: str,
    version: str,
    since_date: date | None = None,
    dev_log_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Generate release notes from dev_log, persist draft release, write CHANGELOG.md."""
    db = get_supabase()

    projects = db.select("projects", filters={"id": project_id})
    if not projects:
        raise HTTPException(status_code=404, detail="Projet introuvable")
    project = projects[0]
    project_name = project["name"]

    dev_log_entries = collect_dev_log_entries(
        db,
        project_id,
        since_date=since_date,
        dev_log_ids=dev_log_ids,
    )
    if not dev_log_entries:
        raise HTTPException(
            status_code=400,
            detail="Aucune entrée dev_log trouvée pour cette sélection.",
        )

    notes = _call_openrouter(project_name, version, dev_log_entries)
    entry_ids = [entry["id"] for entry in dev_log_entries]

    try:
        release_row = db.insert(
            "releases",
            {
                "project_id": project_id,
                "version": version,
                "release_date": date.today().isoformat(),
                "app_store_notes": notes["app_store"],
                "google_play_notes": notes["google_play"],
                "changelog_md": notes["changelog"],
                "dev_log_ids": entry_ids,
                "status": "draft",
            },
        )
    except Exception as exc:
        if _is_missing_table_error(exc, "releases"):
            raise HTTPException(
                status_code=503,
                detail="Table 'releases' absente — appliquer la migration Supabase avant de générer une release.",
            ) from exc
        raise

    project_slug = BrainstormAgent.project_folder_slug(project_name, project_id)
    _write_changelog_file(project_slug, notes["changelog"])

    return {
        "release_id": release_row["id"],
        "app_store_notes": notes["app_store"],
        "google_play_notes": notes["google_play"],
        "changelog_md": notes["changelog"],
        "release": release_row,
    }
