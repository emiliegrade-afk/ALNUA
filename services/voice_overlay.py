"""Voice overlay — second LLM pass: spoken quip, never reread facts (DEC-033)."""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

MAX_OVERLAY_CHARS = 200

_EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
_PHONE_RE = re.compile(
    r"\b(?:\+33|0)[1-9](?:[\s.-]?\d{2}){4}\b"
)
_TIME_RE = re.compile(r"\b\d{1,2}\s*h\s*\d{2}\b", re.I)
_URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
_SIR_RE = re.compile(r"\b(sir|sire)\b", re.I)
_JSONISH_RE = re.compile(r"[{}\[\]]")
_DIGIT_TOKEN_RE = re.compile(r"\b\d{2,}\b")

_ARIA_SPEAK_MARKERS = (
    "relance",
    "relancé",
    "je lance",
    "j'ai lancé",
    "lancé",
    "alerte",
    "bloqué",
    "blocage",
    "échec",
    "erreur",
    "décision",
    "validé",
    "pipeline cass",
    "j'agis",
)

_NADIA_SYSTEM = """Tu es Nadia Faure, secrétaire d'Emilie (CEO ALNUA).
On t'envoie des FAITS déjà envoyés à Emilie en texte.
Ta seule job : 1 ou 2 phrases PARLÉES (tutoiement) — réaction, priorité, prochaine étape.
INTERDIT : relire emails, numéros, heures (12h30), URLs, JSON, corps de mail.
INTERDIT : sir, butler Marvel, « voici ce que tu as demandé ».
Français. Maximum 200 caractères. Texte brut, pas de markdown."""

_ARIA_SYSTEM = """Tu es Aria Voss, COO ALNUA.
On t'envoie des FAITS déjà envoyés à Emilie en texte.
1 ou 2 phrases PARLÉES, directes. Tutoiement. Pas de vanne si c'est cassé ou en échec.
INTERDIT : relire emails, numéros, heures, URLs, JSON.
INTERDIT : sir, butler Marvel.
Français. Maximum 200 caractères. Texte brut, pas de markdown."""


def sensitive_tokens(facts: str) -> set[str]:
    """Tokens from facts that must not appear in the spoken overlay."""
    text = facts or ""
    found: set[str] = set()
    for rx in (_EMAIL_RE, _PHONE_RE, _TIME_RE, _URL_RE):
        found.update(m.group(0).lower() for m in rx.finditer(text))
    found.update(m.group(0) for m in _DIGIT_TOKEN_RE.finditer(text))
    return {t.strip() for t in found if t.strip()}


def leaks_facts(overlay: str, facts: str) -> bool:
    """True if the overlay rereads sensitive facts or uses forbidden register."""
    spoken = (overlay or "").strip()
    if not spoken:
        return True
    if _SIR_RE.search(spoken) or _JSONISH_RE.search(spoken):
        return True
    if _EMAIL_RE.search(spoken) or _PHONE_RE.search(spoken):
        return True
    if _TIME_RE.search(spoken) or _URL_RE.search(spoken):
        return True
    lower = spoken.lower()
    for token in sensitive_tokens(facts):
        if token.lower() in lower:
            return True
    return False


def should_speak_overlay(agent_id: str, facts: str) -> bool:
    """Nadia: speak on useful replies. Aria: only alert / action / decision."""
    body = (facts or "").strip()
    if not body:
        return False
    if body.lstrip().startswith(("❌", "⏱️")):
        return False
    aid = (agent_id or "secretary").strip().lower()
    if aid in {"coo", "aria"}:
        low = body.lower()
        return any(m in low for m in _ARIA_SPEAK_MARKERS)
    return True


def _clean_overlay(raw: str) -> str:
    text = (raw or "").strip().strip("\"'`")
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[*_#>`]", "", text)
    if len(text) > MAX_OVERLAY_CHARS:
        text = text[:MAX_OVERLAY_CHARS].rsplit(" ", 1)[0].rstrip(" ,.;")
    return text.strip()


def _overlay_llm_enabled() -> bool:
    try:
        from config.settings import get_settings

        return bool(get_settings().voice_overlay_llm)
    except Exception:
        return True


def _contextual_fallback(facts: str) -> str | None:
    """Tool-aware quips (weather / brief / research) — still no fact reread."""
    low = (facts or "").lower()
    if any(k in low for k in ("°c", " °c", "ciel ", "pluie", "parapluie", "météo")):
        if "pluie possible" in low or "averse" in low:
            return "Prends un parapluie."
        if "pas de pluie" in low or any(
            k in low for k in ("dégagé", "ensoleill", "clair", "beau", "clear")
        ):
            return "Beau temps. Pas besoin de parapluie."
        if "pluie" in low or "rain" in low:
            return "Prends un parapluie."
        return "La météo est à l'écran."
    if any(
        k in low
        for k in (
            "bonjour emilie",
            "priorité",
            "priorites",
            "briefing du jour",
            "brief matinal",
        )
    ):
        return "Le brief est prêt. Le détail est à l'écran."
    if any(
        k in low
        for k in (
            "recherche lancée",
            "recherche terminee",
            "recherche terminée",
            "recherche approfondie",
        )
    ):
        return "Recherche lancée. Le détail est à l'écran."
    return None


def fallback_overlay(facts: str, *, agent_id: str = "secretary") -> str | None:
    """No-LLM spoken line — never rereads facts. Used when OpenRouter is down."""
    if not should_speak_overlay(agent_id, facts):
        return None
    if (agent_id or "").strip().lower() in {"coo", "aria"}:
        return "J'agis. Le détail est à l'écran."
    line = _contextual_fallback(facts)
    if not line:
        variants = (
            "C'est à l'écran.",
            "Je te l'ai mis devant.",
            "Regarde, c'est affiché.",
        )
        idx = sum(ord(c) for c in (facts or "")[:80]) % len(variants)
        line = variants[idx]
    return None if leaks_facts(line, facts) else line


def spoken_overlay(facts: str, *, agent_id: str = "secretary") -> str | None:
    """LLM overlay, then local fallback. Never raises."""
    if not should_speak_overlay(agent_id, facts):
        return None
    if _overlay_llm_enabled():
        line = generate_overlay(facts, agent_id=agent_id)
        if line:
            return line
    return fallback_overlay(facts, agent_id=agent_id)


def generate_overlay(facts: str, *, agent_id: str = "secretary") -> str | None:
    """Return spoken overlay or None (skip audio). Never raises to caller."""
    body = (facts or "").strip()
    if not should_speak_overlay(agent_id, body):
        return None
    try:
        from agents.base_llm import LLMClient
        from services.input_sanitizer import sanitize_user_input

        safe_facts = sanitize_user_input(
            body[:2500], max_length=2500, redact_pii_enabled=False
        )
        system = _ARIA_SYSTEM if agent_id in {"coo", "aria"} else _NADIA_SYSTEM
        llm_id = "coo" if agent_id in {"coo", "aria"} else "secretary"
        raw = LLMClient().complete(
            system,
            f"Faits déjà affichés à Emilie :\n{safe_facts}\n\nRéplique parlée :",
            agent_id=llm_id,
            method_name="voice_overlay",
            temperature=0.55,
            max_tokens=120,
        )
        overlay = _clean_overlay(raw)
        if leaks_facts(overlay, body):
            logger.info("voice overlay dropped — leaked facts or forbidden register")
            return None
        return overlay or None
    except Exception:
        logger.warning("voice overlay failed", exc_info=True)
        return None
