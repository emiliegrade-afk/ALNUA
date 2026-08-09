"""COO shared constants — aliases, keywords, system prompt."""
from __future__ import annotations

from config.agent_operating_spec import get_system_prompt

COO_SYSTEM_PROMPT = get_system_prompt("coo").strip()

PROJECT_ALIASES: dict[str, str] = {
    "naia": "Naïa",
    "naïa": "Naïa",
    "naya": "Naïa",
    "naima": "Naïa",
    "nuaway": "NUAWAY",
    "nuway": "NUAWAY",
    "nomad": "NUAWAY",
    "nomads": "NUAWAY",
    "vanlife": "NUAWAY",
    "wyrdheim": "Wyrdheim Online",
    "wyrdheim online": "Wyrdheim Online",
    "mmorpg": "Wyrdheim Online",
    "eve": "Eve",
    "robot": "Eve",
    "robotique": "Eve",
    "alnua": "ALNUA",
    "global": "ALNUA",
}

IRREVERSIBLE_KEYWORDS = (
    "publie", "publish", "supprime", "supprimer", "delete", "efface",
    "remove", "envoie le post", "valide la publication",
)

PROJECT_SCOPED_KEYWORDS = (
    "bug", "ticket", "roadmap", "post", "feedback", "feature",
    "crash", "sprint", "priorise", "contenu", "marketing", "spec",
    "cursor", "brainstorm", "idée", "idee",
)

BRANCH_LABELS: dict[str, str] = {
    "app": "App",
    "gaming": "Gaming",
    "robotics": "Robotique",
    "other": "Autre",
}
