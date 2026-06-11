"""Beta tester portal — JWT tokens, project lookup, ticket mapping."""

from __future__ import annotations

import base64
import re
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import HTTPException

from agents.brainstorm_agent import BrainstormAgent
from config.settings import get_settings
from database.supabase_client import SupabaseClient, get_supabase

BETA_STORAGE_BUCKET = "beta-screenshots"
JWT_ALGORITHM = "HS256"
JWT_TTL_DAYS = 365

FEEDBACK_TYPE_TO_TICKET: dict[str, str] = {
    "bug": "bug",
    "crash": "crash",
    "suggestion": "feature",
    "ux": "improvement",
    "autre": "improvement",
}

SEVERITY_TO_PRIORITY: dict[str, str] = {
    "bloquant": "critical",
    "majeur": "high",
    "mineur": "medium",
    "cosmétique": "low",
}


def _jwt_secret() -> str:
    settings = get_settings()
    return settings.supabase_key


def create_tester_token(tester_id: str, project_id: str) -> str:
    payload = {
        "sub": tester_id,
        "project_id": project_id,
        "scope": "beta_tester",
        "exp": datetime.now(UTC) + timedelta(days=JWT_TTL_DAYS),
        "iat": datetime.now(UTC),
    }
    return jwt.encode(payload, _jwt_secret(), algorithm=JWT_ALGORITHM)


def decode_tester_token(token: str) -> dict[str, str]:
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(status_code=401, detail="Token expiré") from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail="Token invalide") from exc

    if payload.get("scope") != "beta_tester":
        raise HTTPException(status_code=401, detail="Token invalide")

    tester_id = payload.get("sub")
    project_id = payload.get("project_id")
    if not tester_id or not project_id:
        raise HTTPException(status_code=401, detail="Token invalide")

    return {"tester_id": str(tester_id), "project_id": str(project_id)}


def resolve_project_by_slug(db: SupabaseClient, project_slug: str) -> dict[str, Any]:
    slug = project_slug.strip().lower()
    projects = db.select("projects", order_by="name")
    for project in projects:
        name_slug = BrainstormAgent.project_folder_slug(project["name"], project["id"])
        if name_slug.lower() == slug:
            return project
    raise HTTPException(status_code=404, detail="Projet introuvable")


def project_slug_for(project: dict[str, Any]) -> str:
    return BrainstormAgent.project_folder_slug(project["name"], project["id"])


def latest_app_version(db: SupabaseClient, project_id: str) -> str | None:
    releases = db.select(
        "releases",
        filters={"project_id": project_id},
        order_by="created_at",
        ascending=False,
        limit=1,
    )
    if releases:
        return releases[0].get("version")
    return None


def upload_screenshot(db: SupabaseClient, screenshot_base64: str, project_id: str) -> str:
    raw = screenshot_base64.strip()
    if raw.startswith("data:"):
        header, _, data = raw.partition(",")
        mime_match = re.match(r"data:([^;]+)", header)
        mime = mime_match.group(1) if mime_match else "image/png"
        content = base64.b64decode(data)
    else:
        mime = "image/png"
        content = base64.b64decode(raw)

    ext = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
        "image/gif": "gif",
    }.get(mime, "png")

    path = f"{project_id}/{uuid.uuid4()}.{ext}"
    db.raw.storage.from_(BETA_STORAGE_BUCKET).upload(
        path,
        content,
        file_options={"content-type": mime, "upsert": "false"},
    )
    return db.raw.storage.from_(BETA_STORAGE_BUCKET).get_public_url(path)


def build_ticket_description(
    description: str,
    device: str | None,
    os_version: str | None,
    app_version: str | None,
    tester_name: str | None,
    tester_email: str | None,
) -> str:
    parts = [description or ""]
    meta: list[str] = []
    if tester_name:
        meta.append(f"Testeuse: {tester_name}")
    if tester_email:
        meta.append(f"Email: {tester_email}")
    if device:
        meta.append(f"Device: {device}")
    if os_version:
        meta.append(f"OS: {os_version}")
    if app_version:
        meta.append(f"Version: {app_version}")
    if meta:
        parts.append("\n\n" + "\n".join(meta))
    return "".join(parts).strip()


def create_feedback_ticket(
    db: SupabaseClient,
    *,
    project_id: str,
    feedback_type: str,
    severity: str | None,
    title: str,
    description: str,
    tester: dict[str, Any],
) -> dict[str, Any]:
    ticket_type = FEEDBACK_TYPE_TO_TICKET.get(feedback_type, "bug")
    priority = SEVERITY_TO_PRIORITY.get(severity or "", "medium")

    return db.insert(
        "tickets",
        {
            "project_id": project_id,
            "type": ticket_type,
            "priority": priority,
            "title": f"[BETA] {title}",
            "description": build_ticket_description(
                description,
                tester.get("device"),
                tester.get("os_version"),
                tester.get("app_version"),
                tester.get("first_name"),
                tester.get("email"),
            ),
            "source": "beta_tester",
            "status": "open",
        },
    )


def get_tester_or_404(db: SupabaseClient, tester_id: str) -> dict[str, Any]:
    rows = db.select("beta_testers", filters={"id": tester_id})
    if not rows:
        raise HTTPException(status_code=404, detail="Testeuse introuvable")
    return rows[0]


def invite_url_for_slug(project_slug: str) -> str:
    base = get_settings().beta_portal_base_url.rstrip("/")
    return f"{base}/beta/{project_slug}"
