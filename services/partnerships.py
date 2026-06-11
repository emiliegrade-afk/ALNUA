"""Partnerships CRM — contracts, affiliate tracking, follow-up reminders."""

from __future__ import annotations

import logging
import os
import re
import secrets
import string
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from database.supabase_client import SupabaseClient, get_supabase

logger = logging.getLogger(__name__)

CONTRACTS_ROOT = Path(r"C:\ALNUA\Contrats")

CONTRACT_SUBDIRS: dict[str, str] = {
    "influencer": "Influenceurs",
    "creator": "Influenceurs",
    "brand": "Marques",
    "affiliate": "Affiliés",
}

AFFILIATE_FALLBACK_URL = "https://alnua.com"


def ensure_contract_dirs() -> None:
    """Create local contract folders on API startup."""
    CONTRACTS_ROOT.mkdir(parents=True, exist_ok=True)
    for sub in CONTRACT_SUBDIRS.values():
        (CONTRACTS_ROOT / sub).mkdir(parents=True, exist_ok=True)


def _sanitize_filename(name: str) -> str:
    cleaned = re.sub(r"[^\w\s-]", "", name, flags=re.UNICODE)
    cleaned = re.sub(r"\s+", "_", cleaned.strip())
    return cleaned[:80] or "partner"


def contract_dir_for_type(partner_type: str) -> Path:
    sub = CONTRACT_SUBDIRS.get(partner_type)
    if sub:
        return CONTRACTS_ROOT / sub
    return CONTRACTS_ROOT


def build_contract_path(partner_name: str, partner_type: str) -> Path:
    today = date.today().isoformat()
    safe_name = _sanitize_filename(partner_name)
    filename = f"{today}_{safe_name}_{partner_type}.pdf"
    return contract_dir_for_type(partner_type) / filename


def generate_affiliate_code(name: str | None = None) -> str:
    """Short memorable code; suffix avoids collisions."""
    base = ""
    if name:
        base = re.sub(r"[^A-Za-z0-9]", "", name.upper())[:8]
    if len(base) < 3:
        base = "ALNUA"
    suffix = "".join(secrets.choice(string.digits) for _ in range(2))
    return f"{base}{suffix}"


def affiliate_public_url(code: str, base_url: str = "https://hub.alnua.com") -> str:
    return f"{base_url.rstrip('/')}/go/{code}"


def parse_audience_size_text(text: str | None) -> int | None:
    """Map public form audience bucket to approximate follower count."""
    if not text:
        return None
    mapping = {
        "< 1k": 500,
        "1k-10k": 5000,
        "10k-100k": 50000,
        "100k+": 150000,
    }
    return mapping.get(text.strip())


def run_partnership_followup_reminders(db: SupabaseClient | None = None) -> int:
    """
    Daily job: create tickets for partners due for follow-up today.
    Skips if an open reminder ticket already exists for the partner.
    """
    db = db or get_supabase()
    today = date.today().isoformat()
    partners = db.select(
        "partners",
        filters=None,
        order_by="next_followup",
        ascending=True,
    )
    due = [
        p
        for p in partners
        if p.get("next_followup") and str(p["next_followup"]) <= today
        and p.get("status") not in ("declined", "paused")
    ]
    created = 0
    for partner in due:
        partner_id = partner["id"]
        title = f"📞 Relance partenariat : {partner.get('name', 'Partenaire')}"
        existing = db.select("tickets", filters={"source": "partnerships_bot"})
        if any(
            t.get("status") in ("open", "in_progress")
            and partner_id in (t.get("description") or "")
            for t in existing
        ):
            continue

        project_id = (partner.get("project_ids") or [None])[0]
        if not project_id:
            projects = db.select("projects", limit=1)
            project_id = projects[0]["id"] if projects else None
        if not project_id:
            logger.warning("No project for partnership reminder ticket")
            continue

        db.insert(
            "tickets",
            {
                "project_id": project_id,
                "type": "reminder",
                "priority": "medium",
                "title": title,
                "description": (
                    f"Relance partenariat due. partner_id={partner_id}\n"
                    f"Email: {partner.get('email') or '—'}\n"
                    f"Notes: {(partner.get('notes') or '')[:500]}"
                ),
                "source": "partnerships_bot",
                "status": "open",
            },
        )
        created += 1
    return created


def record_affiliate_click(
    db: SupabaseClient,
    link: dict[str, Any],
    user_agent: str | None,
    referer: str | None,
) -> None:
    link_id = link["id"]
    current = int(link.get("clicks") or 0)
    db.update("affiliate_links", link_id, {"clicks": current + 1})
    db.insert(
        "affiliate_clicks",
        {
            "link_id": link_id,
            "event_type": "click",
            "user_agent": user_agent,
            "referer": referer,
        },
    )


def record_affiliate_conversion(
    db: SupabaseClient,
    link: dict[str, Any],
    revenue: float = 0.0,
) -> dict[str, Any]:
    link_id = link["id"]
    conversions = int(link.get("conversions") or 0) + 1
    revenue_total = float(link.get("revenue_generated") or 0) + revenue
    updated = db.update(
        "affiliate_links",
        link_id,
        {
            "conversions": conversions,
            "revenue_generated": revenue_total,
        },
    )
    db.insert(
        "affiliate_clicks",
        {
            "link_id": link_id,
            "event_type": "conversion",
            "revenue": revenue,
        },
    )
    return updated


def affiliate_link_timeline(
    db: SupabaseClient,
    link_id: str,
    days: int = 30,
) -> list[dict[str, Any]]:
    """Daily click/conversion counts for charts."""
    since = datetime.now(timezone.utc) - timedelta(days=days - 1)
    rows = (
        db.table("affiliate_clicks")
        .select("clicked_at, event_type")
        .eq("link_id", link_id)
        .gte("clicked_at", since.isoformat())
        .execute()
        .data
        or []
    )
    buckets: dict[str, dict[str, int]] = {}
    for i in range(days):
        d = (date.today() - timedelta(days=days - 1 - i)).isoformat()
        buckets[d] = {"date": d, "clicks": 0, "conversions": 0}

    for row in rows:
        raw = row.get("clicked_at") or ""
        day = raw[:10]
        if day not in buckets:
            continue
        if row.get("event_type") == "conversion":
            buckets[day]["conversions"] += 1
        else:
            buckets[day]["clicks"] += 1

    return list(buckets.values())


def partnership_stats(db: SupabaseClient) -> dict[str, Any]:
    partners = db.select("partners")
    links = db.select("affiliate_links")
    requests = db.select("partnership_requests", order_by="created_at", ascending=False)

    today = date.today().isoformat()
    week_ago = (date.today() - timedelta(days=7)).isoformat()

    total_active = sum(1 for p in partners if p.get("status") == "active")
    total_prospects = sum(
        1 for p in partners if p.get("status") in ("prospect", "contacted", "in_discussion")
    )
    followups_due_today = sum(
        1
        for p in partners
        if p.get("next_followup") and str(p["next_followup"]) <= today
        and p.get("status") not in ("declined", "paused")
    )
    requests_this_week = sum(
        1 for r in requests if (r.get("created_at") or "")[:10] >= week_ago
    )
    new_requests = sum(1 for r in requests if r.get("status") == "new")

    top_affiliates = sorted(
        links,
        key=lambda l: float(l.get("revenue_generated") or 0),
        reverse=True,
    )[:5]

    partner_map = {p["id"]: p for p in partners}
    top_enriched = []
    for link in top_affiliates:
        partner = partner_map.get(link.get("partner_id"), {})
        top_enriched.append(
            {
                **link,
                "partner_name": partner.get("name"),
            }
        )

    return {
        "total_active": total_active,
        "total_prospects": total_prospects,
        "top_affiliates": top_enriched,
        "requests_this_week": requests_this_week,
        "followups_due_today": followups_due_today,
        "new_requests": new_requests,
    }


def open_contract_file(path: str) -> None:
    if not path or not Path(path).is_file():
        raise FileNotFoundError("Contrat introuvable")
    os.startfile(path)  # noqa: S606 — Windows native PDF viewer


def open_contracts_folder() -> None:
    ensure_contract_dirs()
    os.startfile(str(CONTRACTS_ROOT))  # noqa: S606
