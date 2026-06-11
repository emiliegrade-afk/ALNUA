"""Waitlist — project lookup, position, markdown preview."""

from __future__ import annotations

import html
import re
from datetime import UTC, datetime, timedelta
from typing import Any

from agents.base import LLMClient, log_agent_action
from database.supabase_client import SupabaseClient, get_supabase
from services.beta_portal import project_slug_for, resolve_project_by_slug


def waitlist_url_for_slug(project_slug: str) -> str:
    from config.settings import get_settings

    base = get_settings().beta_portal_base_url.rstrip("/")
    return f"{base}/waitlist/{project_slug}"


def compute_position(db: SupabaseClient, project_id: str, entry_id: str) -> tuple[int, int]:
    """Return (position, total) for an entry within its project waitlist."""
    entries = db.select(
        "waitlist",
        filters={"project_id": project_id},
        order_by="created_at",
        ascending=True,
    )
    total = len(entries)
    position = 1
    for i, row in enumerate(entries, start=1):
        if row["id"] == entry_id:
            position = i
            break
    return position, total


def markdown_to_html(message_md: str, *, subject: str = "") -> str:
    """Minimal markdown → HTML for email preview (no external deps)."""
    text = message_md.strip()
    if not text:
        text = ""

    lines = text.splitlines()
    body_parts: list[str] = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                body_parts.append("</ul>")
                in_list = False
            continue

        if stripped.startswith("## "):
            if in_list:
                body_parts.append("</ul>")
                in_list = False
            body_parts.append(f"<h2>{html.escape(stripped[3:])}</h2>")
        elif stripped.startswith("# "):
            if in_list:
                body_parts.append("</ul>")
                in_list = False
            body_parts.append(f"<h1>{html.escape(stripped[2:])}</h1>")
        elif stripped.startswith("- "):
            if not in_list:
                body_parts.append("<ul>")
                in_list = True
            item = _inline_md(stripped[2:])
            body_parts.append(f"<li>{item}</li>")
        else:
            if in_list:
                body_parts.append("</ul>")
                in_list = False
            body_parts.append(f"<p>{_inline_md(stripped)}</p>")

    if in_list:
        body_parts.append("</ul>")

    body_html = "\n".join(body_parts)
    subject_html = html.escape(subject) if subject else "ALNUA"

    return f"""<!DOCTYPE html>
<html lang="fr">
<head><meta charset="utf-8"><title>{subject_html}</title></head>
<body style="font-family: Georgia, serif; max-width: 560px; margin: 0 auto; padding: 24px; color: #1a1a1a; line-height: 1.6;">
  <div style="border-bottom: 2px solid #C08A72; padding-bottom: 12px; margin-bottom: 24px;">
    <span style="font-size: 12px; letter-spacing: 0.15em; color: #C08A72;">ALNUA</span>
  </div>
  {body_html}
  <p style="margin-top: 32px; font-size: 12px; color: #888;">© ALNUA — Tu recevras cet email car tu es inscrite sur notre liste d'attente.</p>
</body>
</html>"""


def _inline_md(text: str) -> str:
    escaped = html.escape(text)
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        r'<a href="\2" style="color:#C08A72">\1</a>',
        escaped,
    )
    return escaped


def generate_waitlist_email(
    db: SupabaseClient,
    project_id: str,
    *,
    llm: LLMClient | None = None,
) -> dict[str, str]:
    """Content Agent generates a waitlist announcement email draft."""
    rows = db.select("projects", filters={"id": project_id})
    if not rows:
        raise ValueError("Projet introuvable")
    project = rows[0]
    project_name = project["name"]
    description = project.get("description") or ""

    client = llm or LLMClient()
    system = """Tu es l'agent contenu d'ALNUA. Rédige un email d'annonce pour les personnes
inscrites sur la liste d'attente d'un projet ALNUA. Ton chaleureux, authentique, en français.
Réponds UNIQUEMENT en JSON valide :
{"subject": "string", "message_md": "string"}
Le message_md utilise du markdown simple (titres ##, listes -, gras **).
Pas de spam, pas de fausses promesses. Mentionne qu'on approche du lancement."""

    user = f"""Projet : {project_name}
Description : {description}
Contexte : email aux inscrites waitlist pour les tenir informées avant le lancement."""

    raw = client.complete(system=system, user=user, temperature=0.75, max_tokens=1200)
    from agents.base import parse_json_response

    data = parse_json_response(raw)
    subject = str(data.get("subject") or f"Bientôt : {project_name}").strip()
    message_md = str(data.get("message_md") or "").strip()

    log_agent_action(
        db,
        agent_name="content_agent",
        action="generate_waitlist_email",
        input_summary=f"project={project_name}",
        output_summary=f"subject={subject[:80]}",
        project_id=project_id,
    )

    return {"subject": subject, "message_md": message_md}


def waitlist_stats(db: SupabaseClient, project_id: str | None = None) -> dict[str, Any]:
    filters = {"project_id": project_id} if project_id else None
    entries = db.select("waitlist", filters=filters, order_by="created_at", ascending=True)

    week_ago = datetime.now(UTC) - timedelta(days=7)
    this_week = 0
    by_source: dict[str, int] = {}
    by_status: dict[str, int] = {}
    timeline: dict[str, int] = {}
    by_project: dict[str, dict[str, Any]] = {}

    projects = {p["id"]: p for p in db.select("projects")}
    today = datetime.now(UTC).date()

    for row in entries:
        pid = row.get("project_id") or ""
        status = row.get("status") or "waiting"
        source = row.get("source") or "direct"
        by_status[status] = by_status.get(status, 0) + 1
        by_source[source] = by_source.get(source, 0) + 1

        created = row.get("created_at")
        if created:
            try:
                dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
                if dt >= week_ago:
                    this_week += 1
                day_key = dt.date().isoformat()
                timeline[day_key] = timeline.get(day_key, 0) + 1

                if pid:
                    bucket = by_project.setdefault(
                        pid,
                        {"total": 0, "this_week": 0, "project_name": projects.get(pid, {}).get("name", "")},
                    )
                    bucket["total"] += 1
                    if dt >= week_ago:
                        bucket["this_week"] += 1
            except ValueError:
                pass

    timeline_7d: list[dict[str, Any]] = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        key = day.isoformat()
        timeline_7d.append({"date": key, "count": timeline.get(key, 0)})

    per_project: list[dict[str, Any]] = []
    for pid, project in projects.items():
        bucket = by_project.get(pid, {"total": 0, "this_week": 0})
        per_project.append({
            "project_id": pid,
            "project_name": project["name"],
            "project_slug": project_slug_for(project),
            "total": bucket.get("total", 0),
            "this_week": bucket.get("this_week", 0),
        })

    return {
        "total": len(entries),
        "this_week": this_week,
        "by_source": by_source,
        "by_status": by_status,
        "timeline_7d": timeline_7d,
        "per_project": per_project,
    }


__all__ = [
    "compute_position",
    "generate_waitlist_email",
    "markdown_to_html",
    "project_slug_for",
    "resolve_project_by_slug",
    "waitlist_stats",
    "waitlist_url_for_slug",
]
