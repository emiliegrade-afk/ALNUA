"""Daily morning briefing — Supabase aggregation + OpenRouter summary."""

from __future__ import annotations

import json
import logging
from datetime import date, timedelta
from typing import Any

import httpx

from config.settings import get_settings
from database.supabase_client import SupabaseClient, get_supabase

logger = logging.getLogger(__name__)

BRIEFING_MODEL = "anthropic/claude-3-haiku"

SYSTEM_PROMPT = (
    "Tu es l'assistant COO d'Emilie, dev solo chez ALNUA. "
    "Tu génères des briefings matinaux concis et actionnables. "
    "Ton ton : direct, bienveillant, pro. Pas de blabla."
)

USER_PROMPT_TEMPLATE = (
    "Voici les données du jour : {data_json}.\n"
    "Génère un briefing structuré avec ces sections :\n"
    "🔥 Urgent (si tickets critical/high ouverts)\n"
    "⏳ En attente de toi (posts à approuver, décisions à prendre)\n"
    "📅 Échéances proches (roadmap items)\n"
    "✅ Bon à savoir (activité récente positive)\n"
    "Si une section est vide, omets-la.\n"
    "Maximum 150 mots total. Pas de markdown lourd."
)


def _project_name_map(db: SupabaseClient) -> dict[str, str]:
    projects = db.select("projects", columns="id, name")
    return {p["id"]: p["name"] for p in projects}


def _attach_project_names(
    rows: list[dict[str, Any]],
    names: dict[str, str],
) -> list[dict[str, Any]]:
    enriched: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        pid = item.get("project_id")
        if pid and pid in names:
            item["project_name"] = names[pid]
        enriched.append(item)
    return enriched


def _collect_urgent_tickets(
    db: SupabaseClient,
    project_id: str | None,
    names: dict[str, str],
) -> list[dict[str, Any]]:
    query = (
        db.table("tickets")
        .select("*")
        .in_("priority", ["critical", "high"])
        .in_("status", ["open", "in_progress"])
        .order("created_at", desc=True)
    )
    if project_id:
        query = query.eq("project_id", project_id)
    response = query.execute()
    return _attach_project_names(response.data or [], names)


def _collect_pending_posts(
    db: SupabaseClient,
    project_id: str | None,
    names: dict[str, str],
) -> list[dict[str, Any]]:
    # Schema uses pending_approval (not "pending")
    query = (
        db.table("posts_queue")
        .select("*")
        .eq("status", "pending_approval")
        .order("scheduled_at", desc=False)
    )
    if project_id:
        query = query.eq("project_id", project_id)
    response = query.execute()
    return _attach_project_names(response.data or [], names)


def _collect_imminent_roadmap(
    db: SupabaseClient,
    project_id: str | None,
    names: dict[str, str],
) -> list[dict[str, Any]]:
    today = date.today()
    horizon = (today + timedelta(days=7)).isoformat()
    query = (
        db.table("roadmap")
        .select("*")
        .neq("status", "done")
        .not_.is_("due_date", "null")
        .lte("due_date", horizon)
        .order("due_date", desc=False)
    )
    if project_id:
        query = query.eq("project_id", project_id)
    response = query.execute()
    rows = response.data or []
    # Exclude past-due items still open are included (due_date <= horizon covers them)
    return _attach_project_names(rows, names)


def _collect_recent_dev_log(
    db: SupabaseClient,
    project_id: str | None,
    names: dict[str, str],
) -> list[dict[str, Any]]:
    query = db.table("dev_log").select("*").order("created_at", desc=True).limit(3)
    if project_id:
        query = query.eq("project_id", project_id)
    response = query.execute()
    return _attach_project_names(response.data or [], names)


def _collect_analytics_anomalies(
    db: SupabaseClient,
    project_id: str | None,
    names: dict[str, str],
) -> list[dict[str, Any]]:
    today = date.today()
    yesterday = today - timedelta(days=1)
    query = (
        db.table("analytics")
        .select("*")
        .in_("date", [today.isoformat(), yesterday.isoformat()])
    )
    if project_id:
        query = query.eq("project_id", project_id)
    response = query.execute()
    rows = response.data or []
    if not rows:
        return []

    by_key: dict[tuple[str, str, str], dict[str, float]] = {}
    for row in rows:
        key = (row["project_id"], row["metric_name"], row.get("source", ""))
        by_key.setdefault(key, {})[row["date"]] = float(row["value"])

    anomalies: list[dict[str, Any]] = []
    for (pid, metric, source), values in by_key.items():
        prev = values.get(yesterday.isoformat())
        curr = values.get(today.isoformat())
        if prev is None or curr is None or prev <= 0:
            continue
        drop_pct = ((prev - curr) / prev) * 100
        if drop_pct > 20:
            anomalies.append(
                {
                    "project_id": pid,
                    "project_name": names.get(pid, "—"),
                    "metric_name": metric,
                    "source": source,
                    "yesterday": prev,
                    "today": curr,
                    "drop_pct": round(drop_pct, 1),
                }
            )
    return anomalies


def collect_briefing_data(
    db: SupabaseClient,
    project_id: str | None = None,
) -> dict[str, Any]:
    """Aggregate raw inputs for the daily briefing."""
    names = _project_name_map(db)
    tickets = _collect_urgent_tickets(db, project_id, names)
    posts = _collect_pending_posts(db, project_id, names)
    roadmap = _collect_imminent_roadmap(db, project_id, names)
    dev_log = _collect_recent_dev_log(db, project_id, names)
    analytics = _collect_analytics_anomalies(db, project_id, names)

    return {
        "tickets": tickets,
        "posts": posts,
        "roadmap": roadmap,
        "dev_log": dev_log,
        "analytics_anomalies": analytics,
    }


def _call_openrouter_summary(raw_data: dict[str, Any]) -> str:
    settings = get_settings()
    if not settings.openrouter_api_key.strip():
        return _fallback_summary(raw_data)

    payload = {
        "model": BRIEFING_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": USER_PROMPT_TEMPLATE.format(
                    data_json=json.dumps(raw_data, ensure_ascii=False, default=str)
                ),
            },
        ],
        "temperature": 0.4,
        "max_tokens": 512,
    }
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://alnua-hub.local",
        "X-Title": "ALNUA Hub Daily Briefing",
    }

    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                f"{settings.openrouter_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
        return data["choices"][0]["message"]["content"].strip()
    except Exception:
        logger.exception("OpenRouter briefing generation failed")
        return _fallback_summary(raw_data)


def _fallback_summary(raw_data: dict[str, Any]) -> str:
    """Deterministic summary when LLM is unavailable."""
    lines: list[str] = []
    tickets = raw_data.get("tickets") or []
    posts = raw_data.get("posts") or []
    roadmap = raw_data.get("roadmap") or []
    dev_log = raw_data.get("dev_log") or []

    if tickets:
        lines.append(f"🔥 Urgent — {len(tickets)} ticket(s) critical/high ouverts.")
    if posts:
        lines.append(f"⏳ En attente — {len(posts)} post(s) à approuver.")
    if roadmap:
        lines.append(f"📅 Échéances — {len(roadmap)} item(s) roadmap dans les 7 jours.")
    if dev_log:
        lines.append(f"✅ Activité — {len(dev_log)} entrée(s) dev_log récentes.")
    if not lines:
        lines.append("✅ Rien d'urgent ce matin — bonne journée !")
    return "\n".join(lines)


def generate_daily_briefing(project_id: str | None = None) -> dict[str, Any]:
    """Collect data, call LLM, return briefing payload (not persisted)."""
    db = get_supabase()
    raw_data = collect_briefing_data(db, project_id)
    tickets = raw_data["tickets"]
    posts = raw_data["posts"]
    summary = _call_openrouter_summary(raw_data)

    return {
        "date": date.today().isoformat(),
        "summary": summary,
        "raw_data": raw_data,
        "has_urgent": len(tickets) > 0,
        "urgent_count": len(tickets),
        "pending_count": len(posts),
    }


def get_briefing_for_date(
    db: SupabaseClient,
    target_date: date,
) -> dict[str, Any] | None:
    rows = (
        db.table("daily_briefings")
        .select("*")
        .eq("date", target_date.isoformat())
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    data = rows.data or []
    return data[0] if data else None


def store_daily_briefing(
    db: SupabaseClient,
    briefing: dict[str, Any],
    *,
    replace_existing: bool = False,
) -> dict[str, Any]:
    """Persist briefing; update today's row when replace_existing is set."""
    row_data = {
        "date": briefing["date"],
        "summary": briefing["summary"],
        "raw_data": briefing["raw_data"],
        "has_urgent": briefing["has_urgent"],
        "urgent_count": briefing["urgent_count"],
        "pending_count": briefing["pending_count"],
    }
    if replace_existing:
        existing = get_briefing_for_date(db, date.fromisoformat(briefing["date"]))
        if existing:
            return db.update("daily_briefings", existing["id"], row_data)

    return db.insert("daily_briefings", row_data)


def generate_and_store_daily_briefing(
    project_id: str | None = None,
    *,
    skip_if_exists: bool = False,
    replace_existing: bool = False,
) -> dict[str, Any]:
    """Generate briefing and save to Supabase."""
    db = get_supabase()
    today = date.today()

    if skip_if_exists and get_briefing_for_date(db, today):
        existing = get_briefing_for_date(db, today)
        assert existing is not None
        return existing

    briefing = generate_daily_briefing(project_id)
    return store_daily_briefing(db, briefing, replace_existing=replace_existing)
