"""
skill_content_company.py — Corporate brand voice & cross-sector review for ALNUA.

Agents: Anouk Gerard (content_company)
Maintains brand voice guide, reviews sector posts for tone consistency,
manages LinkedIn/X corporate accounts.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

BRAND_VOICE_GUIDE: dict[str, str] = {
    "who": "ALNUA — entreprise tech multi-produits pilotée par IA, fondée par Emilie (CEO)",
    "tone": "inspirant, professionnel, jamais arrogant",
    "values": "build-in-public, transparence, solo founder CEO, IA pragmatique",
    "forbidden": (
        "corporate slop (revolutionize, disrupt, synergy), promesses vides, jargon, "
        "storytelling mode de vie / nomadisme comme identité ALNUA (NUAWAY = un produit, pas la marque)"
    ),
    "ceo_voice": "Emilie parle en CEO solopreneuse : direct, honnête, sans cadrer la société sur un lifestyle",
}


def review_post_for_brand_voice(post_text: str, sector: str = "") -> dict[str, Any]:
    """Validate a post against the ALNUA brand voice guide. Returns flags if issues found."""
    flags: list[str] = []
    lower = post_text.lower()
    forbidden_words = ["revolutionize", "disrupt", "synergy", "game-changer", "unprecedented"]
    for word in forbidden_words:
        if word in lower:
            flags.append(f"forbidden_word:{word}")

    return {
        "ok": len(flags) == 0,
        "flags": flags,
        "sector": sector,
        "preview": post_text[:200],
    }


def gen_corporate_announcement(
    topic: str,
    milestone_type: str = "milestone",
) -> dict[str, Any]:
    """Draft a corporate announcement (hiring, funding, partnership, product launch)."""
    templates: dict[str, str] = {
        "milestone": "🚀 [Milestone] — ALNUA vient de franchir [quoi]. Détail dans le fil.",
        "hiring": "👋 ALNUA recrute — [poste]. On construit [quoi] avec des agents IA. DM ouverts.",
        "funding": "💰 [Montant] levé pour [objectif]. Merci à [investisseurs]. On construit la suite.",
        "partnership": "🤝 ALNUA × [partenaire] — [objet]. Annonce commune à venir.",
    }
    template = templates.get(milestone_type, templates["milestone"])
    return {
        "platform": "linkedin",
        "content_type": "announcement",
        "draft": template,
        "topic": topic,
        "type": milestone_type,
        "author": "Anouk Gerard",
    }