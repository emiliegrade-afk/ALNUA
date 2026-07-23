"""Natural-language intents for Nadia (secretary) — Telegram + Hub assistant."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

_PARIS = ZoneInfo("Europe/Paris")

NIGHT_REPORT_MARKERS = (
    "rapport de la nuit",
    "rapport nuit",
    "cette nuit",
    "pendant la nuit",
    "qu'est-ce qui s'est passé",
    "quest ce qui sest passe",
    "qu'est il passé",
    "résumé de la nuit",
    "resume de la nuit",
    "bilan de la nuit",
    "cette matinée",
    "depuis hier soir",
)

BRIEFING_MARKERS = (
    "briefing du jour",
    "brief du jour",
    "briefing matin",
    "résumé du matin",
    "resume du matin",
    "priorités du jour",
    "priorites du jour",
    "quoi de neuf aujourd",
)

EMAIL_MARKERS = (
    "rédige un email",
    "redige un email",
    "rédige un mail",
    "écris un email",
    "ecris un email",
    "mail à ",
    "mail a ",
    "email à ",
    "email a ",
)

CONTRACT_MARKERS = (
    "rédige un contrat",
    "redige un contrat",
    "brouillon de contrat",
    "contrat nda",
    " nda ",
    "contrat de ",
)

MEETING_MARKERS = (
    "planifie une réunion",
    "planifie une reunion",
    "organise une réunion",
    "organise une reunion",
    "ordre du jour",
    "compte rendu",
    "cr de réunion",
    "cr de reunion",
    "notes de réunion",
)

CONNECT_MARKERS = (
    "connecte gmail",
    "connecter gmail",
    "connecte mon gmail",
    "connecte le calendrier",
    "connecte google calendar",
    "connecter mon calendrier",
    "oauth gmail",
    "lier gmail",
    "lier mon agenda",
)

INBOX_MARKERS = (
    "mes emails",
    "mes mails",
    "boîte mail",
    "boite mail",
    "trier mes emails",
    "trier mes mails",
    "emails urgents",
    "courrier entrant",
    "derniers emails",
)

SEND_CONFIRM_MARKERS = (
    "envoie le mail",
    "envoie le email",
    "envoyer le mail",
    "confirme l'envoi",
    "confirme l envoi",
    "oui envoie",
    "valide l'envoi",
    "valide l envoi",
    "envoie maintenant",
)

CALENDAR_MARKERS = (
    "mon agenda",
    "mon planning",
    "créneaux libres",
    "creneaux libres",
    "réunion demain",
    "reunion demain",
    "événements aujourd",
    "evenements aujourd",
    "calendrier",
)

ACADEMY_MARKERS = (
    "academy",
    "académie",
    "academie",
    "exercice",
    "exercices",
    "pipeline academy",
    "pipeline de l'academy",
    "progression academy",
    "où en est l'academy",
    "ou en est l'academy",
    "c'est quoi l'academy",
    "quest ce que l'academy",
    "parcours academy",
)

WAKE_OPS_MARKERS = (
    "relance théo",
    "relance theo",
    "relancer théo",
    "relancer theo",
    "réveille théo",
    "reveille theo",
    "réveille les agents",
    "reveille les agents",
    "wake agents",
    "relance le pipeline",
    "relancer le pipeline",
    "relance academy",
    "relancer academy",
    "relance le codage",
    "relancer le codage",
    "remets théo",
    "remets theo",
)

ARIA_DELEGATION_MARKERS = (
    "demande à aria",
    "demande a aria",
    "dis à aria",
    "dis a aria",
    "passe à aria",
    "passe a aria",
    "transmets à aria",
    "transmets a aria",
    "fais dire à aria",
    "fais dire a aria",
    "aria doit",
    "aria peut",
    "via aria",
    "parle à aria",
    "parle a aria",
)

RESEARCH_MARKERS = (
    "recherche ",
    "rechercher ",
    "cherche sur ",
    "trouve des infos",
    "dernières sorties",
    "dernieres sorties",
    "nouveautés ia",
    "nouveautes ia",
    "tendances ",
    "investigue ",
    "investiguer ",
    "bibliothèque",
    "bibliotheque",
    "rapport bibliothèque",
    "rapport bibliotheque",
)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower().strip())


def detect_night_report(text: str) -> bool:
    n = _norm(text)
    return any(m in n for m in NIGHT_REPORT_MARKERS)


def detect_briefing(text: str) -> bool:
    n = _norm(text)
    return any(m in n for m in BRIEFING_MARKERS)


def detect_email_intent(text: str) -> bool:
    return any(m in _norm(text) for m in EMAIL_MARKERS)


def detect_contract_intent(text: str) -> bool:
    return any(m in _norm(text) for m in CONTRACT_MARKERS)


def detect_meeting_intent(text: str) -> bool:
    return any(m in _norm(text) for m in MEETING_MARKERS)


def detect_connect_intent(text: str) -> bool:
    return any(m in _norm(text) for m in CONNECT_MARKERS)


def detect_inbox_intent(text: str) -> bool:
    return any(m in _norm(text) for m in INBOX_MARKERS)


def detect_send_confirm(text: str) -> bool:
    return any(m in _norm(text) for m in SEND_CONFIRM_MARKERS)


def detect_calendar_intent(text: str) -> bool:
    n = _norm(text)
    return any(m in n for m in CALENDAR_MARKERS)


def detect_academy_intent(text: str) -> bool:
    return any(m in _norm(text) for m in ACADEMY_MARKERS)


def detect_wake_ops(text: str) -> bool:
    return any(m in _norm(text) for m in WAKE_OPS_MARKERS)


def detect_aria_delegation(text: str) -> bool:
    return any(m in _norm(text) for m in ARIA_DELEGATION_MARKERS)


def detect_research_intent(text: str) -> bool:
    n = _norm(text)
    if "rapport biblioth" in n:
        return True
    return any(m in n for m in RESEARCH_MARKERS)


def extract_research_query(text: str) -> str:
    """Pull research topic from natural language."""
    raw = text.strip()
    patterns = (
        r"recherche(?:r)?\s+(?:sur\s+)?(.+)$",
        r"cherche\s+(?:sur\s+)?(.+)$",
        r"investigue(?:r)?\s+(?:sur\s+)?(.+)$",
        r"tendances\s+(.+)$",
        r"nouveautés?\s+(.+)$",
        r"nouveautes?\s+(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.I)
        if match:
            topic = match.group(1).strip(" :.-")
            if len(topic) >= 3:
                return topic
    if "rapport biblioth" in _norm(raw):
        return "__report__"
    return raw[:400]


def extract_aria_delegation_message(text: str) -> str:
    """Strip relay phrasing so COO gets the actionable instruction."""
    n = text.strip()
    patterns = (
        r"^(?:demande|dis|passe|transmets|fais dire)\s+(?:à|a)\s+aria\s+(?:de\s+)?",
        r"^aria\s+(?:doit|peut)\s+",
        r"^(?:parle|via)\s+(?:à|a)\s+aria\s+(?:pour\s+)?",
    )
    for pattern in patterns:
        n = re.sub(pattern, "", n, flags=re.I).strip()
    return n or text.strip()


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
        import os

        import httpx

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


def format_json_reply(data: dict[str, Any], *, kind: str) -> str:
    """Turn structured secretary output into chat-friendly text."""
    if kind == "email":
        return (
            f"**Objet :** {data.get('subject', '—')}\n\n"
            f"{data.get('body', '')}\n\n"
            f"_Envoi suggéré : {data.get('suggested_send_time', 'matin')}_"
        )
    if kind == "contract":
        articles = data.get("articles") or []
        body = data.get("preamble", "")
        if articles:
            body += "\n\n" + "\n\n".join(
                f"**Art. {a.get('number')} — {a.get('title')}**\n{a.get('content', '')}"
                for a in articles[:4]
            )
            if len(articles) > 4:
                body += f"\n\n_… et {len(articles) - 4} articles supplémentaires (voir Hub)._"
        return f"**{data.get('title', 'Contrat')}**\n\n{body}"
    if kind == "meeting":
        agenda = data.get("agenda") or []
        items = "\n".join(
            f"• {a.get('time', '?')} ({a.get('duration', '?')} min) — {a.get('item', '')}"
            for a in agenda[:8]
        )
        return (
            f"**{data.get('title', 'Réunion')}**\n"
            f"{data.get('objective', '')}\n\n"
            f"**Ordre du jour :**\n{items}"
        )
    if kind == "notes":
        actions = data.get("action_items") or []
        act = "\n".join(
            f"• {a.get('action', '')} → {a.get('owner', '?')} ({a.get('deadline', '?')})"
            for a in actions[:6]
        )
        return (
            f"**{data.get('title', 'Compte rendu')}**\n\n"
            f"{data.get('summary', '')}\n\n"
            f"**Actions :**\n{act or '—'}"
        )
    return str(data)
