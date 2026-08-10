"""R&D committee agent — routing regexes and keyword maps."""
from __future__ import annotations

import re

MENTION_RE = re.compile(r"@(\w+)", re.IGNORECASE)
REPORT_INTENT_RE = re.compile(
    r"fais.?moi le dossier|génère.?le cr|genere.?le cr|compte.?rendu|"
    r"synthèse de clôture|synthese de cloture|handoff ceo|dossier ceo",
    re.IGNORECASE,
)

KEYWORD_ROUTING: list[tuple[re.Pattern[str], list[str]]] = [
    (re.compile(r"financ|prix|tarif|revenu|roi|capex|business", re.I), ["accounting", "pm"]),
    (re.compile(r"techni|stack|mvp|code|api|supabase|faisabilit", re.I), ["spec", "dev_app"]),
    (re.compile(r"marché|concurrent|positionn|acquisition|go-to-market", re.I), ["marketing", "pm"]),
    (re.compile(r"social|teaser|communaut|contenu|lancement", re.I), ["content", "marketing"]),
    (re.compile(r"jeu|gameplay|joueur|lore", re.I), ["game_director", "dev_gaming"]),
    (re.compile(r"hardware|firmware|capteur|bom|fabrication", re.I), ["hardware", "embedded_dev"]),
]
