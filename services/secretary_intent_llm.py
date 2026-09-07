"""LLM-first intent classification for Nadia (real NL, not keyword-only)."""

from __future__ import annotations

import logging
from typing import Any

from agents.base import LLMClient, parse_json_response
from services.input_sanitizer import sanitize_user_input

logger = logging.getLogger(__name__)

INTENT_VALUES = frozenset(
    {
        "conversation",
        "send_confirm",
        "connect",
        "inbox",
        "calendar",
        "night_report",
        "briefing",
        "wake_ops",
        "research",
        "aria_delegation",
        "academy",
        "email",
        "contract",
        "meeting",
        "ask_lawyer",
        "write_doc",
        "housekeep",
        "weather",
    }
)

_CLASSIFY_PROMPT = """Tu es le routeur d'intentions de Nadia Faure, assistante personnelle d'Emilie (CEO ALNUA).

Message d'Emilie :
\"\"\"
{message}
\"\"\"

Choisis UNE intention parmi :
- conversation — question ouverte, conseil, brainstorm, explication, tout ce qui n'est pas une action outil précise
- send_confirm — confirme l'envoi d'un mail déjà préparé (« envoie », « envoie le mail »)
- connect — connecter Gmail / Calendar
- inbox — lire / trier la boîte mail
- calendar — agenda, créneaux, disponibilités
- night_report — rapport de nuit / bilan overnight Academy
- briefing — priorités / brief du jour / au programme
- wake_ops — relancer le pipeline / Théo / coding Academy
- research — recherche web / deep research / bibliothèque
- aria_delegation — transmettre explicitement à Aria (COO)
- academy — statut Academy / progression exercices
- email — rédiger / préparer un mail
- contract — rédiger / préparer un contrat
- meeting — planifier réunion / notes de réunion
- ask_lawyer — avis juridique / faire relire par l'avocat d'entreprise
- write_doc — créer / éditer un document texte (note, contrat brouillon, compte-rendu)
- housekeep — ranger le PC, trier le bureau, quarantaine, bordel fichiers
- weather — météo d'une ville (temps, pluie, parapluie)

Paraphrases OK (ex. « remets Théo au boulot » → wake_ops ; « c'est quoi le plan aujourd'hui ? » → briefing ;
« range mon bureau » → housekeep ; « ouvre un doc pour le NDA » → write_doc ;
« quel temps à Paris » → weather).
Si doute → conversation.

JSON uniquement :
{{"intent":"...","confidence":0.0,"slots":{{}},"reason":"..."}}
"""


def classify_secretary_intent(message: str) -> dict[str, Any]:
    """
    Return {intent, confidence, slots, reason}.
    On failure → conversation with low confidence.
    """
    clean = sanitize_user_input(message or "", max_length=4000, redact_pii_enabled=False)
    if not clean.strip():
        return {"intent": "conversation", "confidence": 0.0, "slots": {}, "reason": "empty"}

    try:
        llm = LLMClient()
        raw = llm.complete(
            "Tu classifies des intentions. Réponds uniquement en JSON valide.",
            _CLASSIFY_PROMPT.format(message=clean[:3500]),
            agent_id="secretary",
            temperature=0.1,
            max_tokens=400,
        )
        data = parse_json_response(raw)
        if not isinstance(data, dict):
            raise ValueError("not a dict")
        intent = str(data.get("intent") or "conversation").strip().lower()
        if intent not in INTENT_VALUES:
            intent = "conversation"
        try:
            confidence = float(data.get("confidence") or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0
        confidence = max(0.0, min(1.0, confidence))
        slots = data.get("slots") if isinstance(data.get("slots"), dict) else {}
        reason = str(data.get("reason") or "")[:200]
        return {
            "intent": intent,
            "confidence": confidence,
            "slots": slots,
            "reason": reason,
        }
    except Exception as exc:
        logger.warning("secretary intent LLM failed: %s", exc)
        from services.secretary_intents_detect import keyword_fallback_intent

        kw = keyword_fallback_intent(clean)
        if kw:
            return {
                "intent": kw,
                "confidence": 0.72,
                "slots": {},
                "reason": f"keyword:{type(exc).__name__}",
            }
        return {
            "intent": "conversation",
            "confidence": 0.0,
            "slots": {},
            "reason": f"fallback:{exc}",
        }


def should_dispatch_tool(intent: str, confidence: float, *, min_confidence: float = 0.55) -> bool:
    """Tool intents need enough confidence; conversation always 'dispatches' to chat."""
    if intent == "conversation":
        return True
    return confidence >= min_confidence
