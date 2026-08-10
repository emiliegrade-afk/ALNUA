"""Morning/night brief builders for Nadia (secretary)."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import httpx

_PARIS = ZoneInfo("Europe/Paris")


def build_academy_status_brief() -> str:
    """CEO-friendly Academy context — pipeline + progression."""
    lines: list[str] = [
        "📚 **ALNUA Academy** — parcours mobile (Expo) qui forme les agents avant le produit Lounge.",
        "• **Théo** (dev_app) code les exercices GitHub",
        "• **Aria** (COO) coordonne ops et pipeline",
        "• **Nadia** (moi) : ta secrétaire — tes mails, ton planning, tes rapports",
        "",
    ]
    try:
        from services.agent_wake import get_pipeline_status

        status = get_pipeline_status()
        ac = status.get("academy") or {}
        lines.append(f"**Pipeline** : {status.get('message', '—')}")
        if ac:
            lines.append(
                f"• Niveau {ac.get('current_level', '?')} : "
                f"{ac.get('completed', '?')}/{ac.get('total', 52)} exercices"
            )
            lines.append(
                f"• En cours : {ac.get('in_pipeline', 0)} | "
                f"En file : {ac.get('agent_ready', 0)} | "
                f"Échecs : {ac.get('agent_failed', 0)}"
            )
    except Exception:
        lines.append("**Pipeline** : données indisponibles (Hub à redémarrer ?)")

    lines.append("")
    lines.append(
        "_Dis « relance Théo » ou « demande à Aria de relancer le pipeline » pour relancer le codage._"
    )
    return "\n".join(lines)


def build_combined_morning_message() -> str:
    """Single 8h Telegram digest — Nadia voice, priorities + night stats."""
    brief = build_morning_brief_for_secretary()
    night = build_night_report()
    return f"{brief}\n\n---\n\n{night}"


def build_night_report() -> str:
    """CEO-friendly overnight summary — Academy pipeline + progression."""
    lines: list[str] = []
    now = datetime.now(timezone.utc)
    paris_now = now.astimezone(_PARIS)
    lines.append(f"📋 Rapport de nuit — {paris_now.strftime('%d/%m/%Y %H:%M')} (Paris)")
    lines.append("")

    try:
        from services.agent_wake import get_pipeline_status

        status = get_pipeline_status()
        ac = status.get("academy") or {}
        lines.append(f"**Pipeline Academy** : {status.get('message', '—')}")
        if ac:
            lines.append(
                f"• Progression L{ac.get('current_level', '?')} : "
                f"{ac.get('completed', '?')}/{ac.get('total', 52)} exercices"
            )
            lines.append(
                f"• En cours : {ac.get('in_pipeline', 0)} | "
                f"En file : {ac.get('agent_ready', 0)} | "
                f"Échecs : {ac.get('agent_failed', 0)}"
            )
    except Exception:
        lines.append("• Pipeline : données indisponibles (Hub à redémarrer ?)")

    lines.append("")
    try:
        from services.academy_progress import load_progress

        progress = load_progress()
        lv = progress.get("levels", {}).get("2") or {}
        lines.append(
            f"**Niveau 2** : {lv.get('done', 0)}/{lv.get('total', 12)} faits, "
            f"{lv.get('failed', 0)} échec(s)"
        )
        gate = progress.get("gate_academy") or progress.get("gate_nuaway") or {}
        lines.append(f"**Gate Academy** : {gate.get('readiness_pct', '?')}% — ")
        lines.append("ouverte ✅" if gate.get("gate_open") else "fermée 🔒")
    except Exception:
        pass

    lines.append("")
    try:
        token = os.getenv("GITHUB_TOKEN", "").strip()
        repo = os.getenv("GITHUB_REPO_ACADEMY", "emiliegrade-afk/alnua-academy").strip()
        if token and repo:
            since = (now - timedelta(hours=14)).isoformat()
            url = f"https://api.github.com/repos/{repo}/pulls"
            headers = {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            }
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(
                    url,
                    headers=headers,
                    params={"state": "closed", "sort": "updated", "direction": "desc", "per_page": 15},
                )
                resp.raise_for_status()
                merged = [
                    pr
                    for pr in resp.json()
                    if pr.get("merged_at") and pr["merged_at"] >= since
                ]
            if merged:
                lines.append(f"**PR mergées (14h)** : {len(merged)}")
                for pr in merged[:6]:
                    lines.append(f"  • #{pr['number']} {pr['title'][:55]}")
            else:
                lines.append("**PR mergées (14h)** : aucune")
    except Exception:
        lines.append("**GitHub** : historique PR indisponible")

    lines.append("")
    lines.append(
        "_Je reste dispo pour ton planning, tes mails, ou un rapport Academy._"
    )
    return "\n".join(lines)


def build_morning_brief_for_secretary() -> str:
    """Lighter morning brief — Nadia voice, delegates data to COO briefing when possible."""
    try:
        from services.daily_briefing import run_daily_briefing

        result = run_daily_briefing(
            context="Brief matinal pour Emilie — ton secrétariat, concis.",
            include_trends=False,
            include_costs=True,
            include_events=True,
        )
        brief = (result or {}).get("coo_brief") or {}
        if brief.get("headline"):
            parts = [
                "☀️ Bonjour Emilie — Nadia ici.",
                "",
                brief.get("headline", ""),
                "",
                f"1. {brief.get('priority_1', '')}",
                f"2. {brief.get('priority_2', '')}",
                f"3. {brief.get('priority_3', '')}",
            ]
            alerts = brief.get("alerts") or []
            if alerts:
                parts.append("")
                parts.append("⚠️ À traiter :")
                parts.extend(f"• {a}" for a in alerts[:4])
            return "\n".join(p for p in parts if p)
    except Exception:
        pass

    return (
        "☀️ Bonjour Emilie — je n'ai pas pu charger le briefing complet.\n"
        "Demande « rapport de la nuit » pour l'Academy, ou parle à Aria pour la coordination ops."
    )
