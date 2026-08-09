"""COO intent detection helpers — extracted from coo_agent (Vague 2 / BUG-004)."""

from __future__ import annotations

import re
from typing import Any

CODING_KEYWORDS = (
    "code", "crée", "cree", "développe", "developpe", "ajoute", "implémente",
    "implemente", "fix", "corrige", "répare", "repare", "refactorise",
    "optimise", "feature", "fonctionnalité", "fonctionnalite", "écran", "ecran",
    "page", "composant",
)

RESEARCH_KEYWORDS = (
    "recherche", "veille", "renseigne", "cherche sur", "trouve des infos",
    "mets à jour", "apprends", "investiguer", "investigue",
)
TEACH_KEYWORDS = ("apprends à", "enseigne", "dis à", "informe", "leçon pour", "donne cette info")
RND_KEYWORDS = (
    "explore l'idée", "idée r&d", "lance un cycle r&d", "rapport r&d",
    "meilleures idées", "fil conducteur r&d", "change le focus r&d",
)

_PLAN_EXECUTION_MARKERS = (
    "faisabilité", "faisabilite", "roi", "retour sur investissement", "rentabilité",
    "analyse", "étude", "etude", "évalue", "evalue", "prépare", "prepare",
    "lance", "délègue", "delegue", "organise", "planifie", "campagne",
    "stratégie", "strategie", "priorise", "triage", "génère un", "genere un",
    "brief", "étude de marché", "market analysis",
    "relance", "relancer", "réveille", "reveille",
)
_BRIEF_ONLY_MARKERS = (
    "urgent aujourd", "qu'est-ce qui est urgent", "état des projets",
    "statut des projets", "briefing du jour", "résumé du jour",
)


def _is_standalone_rnd_research(instruction: str) -> bool:
    """True when the message is R&D/veille without an explicit product target."""
    lower = instruction.lower()
    rnd_markers = (
        "r&d", "rnd", "investiguer", "investigue", "veille sur", "recherche pour r",
        "recherche r&d", "cycle r&d", "fil conducteur r&d",
    )
    product_markers = (
        "nuaway", "nomad", "vanlife", "park4night", "naïa", "naia",
        "wyrdheim", "eve", "creatorflow",
    )
    return any(m in lower for m in rnd_markers) and not any(m in lower for m in product_markers)


def _needs_plan_execution(instruction: str) -> bool:
    """True when the COO must run agents for real, not only chat."""
    lower = instruction.lower()
    if any(kw in lower for kw in _BRIEF_ONLY_MARKERS):
        return False
    return any(kw in lower for kw in _PLAN_EXECUTION_MARKERS)


def _format_plan_execution_result(result: dict[str, Any]) -> str:
    """Turn plan_executor output into a short COO reply."""
    if result.get("error") and not result.get("results"):
        return f"❌ Plan non exécuté : {result['error']}"

    lines = [f"✅ Plan exécuté — {result.get('title', 'objectif')}"]
    for step in result.get("results", [])[:6]:
        agent = step.get("agent_id", "?")
        desc = step.get("description", "")[:60]
        if step.get("success"):
            lines.append(f"• {agent} : {desc} ✓")
        else:
            err = (step.get("error") or "échec")[:80]
            lines.append(f"• {agent} : {desc} — {err}")

    failed = result.get("failure_count", 0)
    if failed:
        lines.append(f"\n⚠️ {failed} étape(s) en échec — vérifie les logs agents.")
    return "\n".join(lines)[:3500]


def _detect_research_intent(msg: str) -> tuple[bool, str | None]:
    """Détecte si l'instruction est une demande de recherche web. Retourne (bool, agent_cible)."""
    msg_lower = msg.lower()
    if not any(kw in msg_lower for kw in RESEARCH_KEYWORDS):
        return False, None
    agent_map = {
        "marketing": "marketing_agent", "contenu": "content_agent", "content": "content_agent",
        "hardware": "hardware_agent", "embedded": "embedded_dev", "comptable": "accountant_agent",
        "dev app": "dev_app", "dev gaming": "dev_gaming", "game director": "game_director",
        "rnd": "rnd_agent", "r&d": "rnd_agent", "pm": "pm_agent",
    }
    for keyword, agent_id in agent_map.items():
        if keyword in msg_lower:
            return True, agent_id
    return True, None


def _extract_research_topic(instruction: str, agent_id: str | None) -> str | None:
    """Pull a custom topic from a veille/recherche message when present."""
    raw = instruction.strip()
    if not raw:
        return None

    patterns = (
        r"recherche(?:r)?\s+(?:pour\s+)?(?:r&?d|rnd)\s*[:.]?\s*(.+)$",
        r"recherche(?:r)?\s+(?:sur\s+)?(.+)$",
        r"veille\s+(?:sur\s+)?(.+)$",
        r"investiguer\s+(?:sur\s+)?(.+)$",
    )
    for pattern in patterns:
        match = re.search(pattern, raw, flags=re.I)
        if match:
            topic = match.group(1).strip(" :.-")
            topic = re.sub(r"\s+pour\s+(marketing|r&?d|rnd|pm).*$", "", topic, flags=re.I)
            if len(topic) >= 4:
                return topic

    if agent_id:
        return None
    return None


def _detect_teach_intent(msg: str) -> tuple[bool, str | None, str | None]:
    """Détecte si l'instruction est une leçon à injecter. Retourne (bool, agent_cible, contenu)."""
    msg_lower = msg.lower()
    if not any(kw in msg_lower for kw in TEACH_KEYWORDS):
        return False, None, None
    agent_map = {
        "marketing": "marketing_agent", "contenu": "content_agent",
        "hardware": "hardware_agent", "embedded": "embedded_dev",
        "comptable": "accountant_agent", "dev": "dev_app",
    }
    target = None
    for keyword, agent_id in agent_map.items():
        if keyword in msg_lower:
            target = agent_id
            break
    return True, target, msg


def detect_coding_intent(message: str) -> bool:
    """True when the message looks like a dev/coding request."""
    msg = message.lower()
    return any(kw in msg for kw in CODING_KEYWORDS)


def detect_target_repo(message: str) -> str:
    """Resolve repo slug (hub / naia / nomad) from message context."""
    msg = message.lower()
    if "naïa" in msg or "naia" in msg:
        return "naia"
    if "nomad" in msg or "nuaway" in msg:
        return "nomad"
    if any(k in msg for k in ("hub alnua", "alnua hub", "infra interne", "repo hub", "sur le hub")):
        return "hub"
    return "hub"
