"""Comms playbooks — marketing, content."""

from __future__ import annotations

from services.rnd_dispatch_playbook_types import AgentPlaybook

PLAYBOOKS: dict[str, AgentPlaybook] = {
    "marketing": AgentPlaybook(
        pole="comms",
        files=["comms/gtm-strategy.md", "comms/content-calendar.md"],
        description="Stratégie GTM + calendrier contenu 4 semaines",
        template="""Génère deux documents marketing pour le projet {title} :

## Document 1 : gtm-strategy.md
# GTM — {title}
## Positionnement
## Cibles (ICP)
## Canaux prioritaires
## Message clé (1 phrase)
## Métriques de succès

---
## Document 2 : content-calendar.md
# Calendrier contenu — {title} (4 semaines)
| Semaine | Canal | Format | Sujet | Objectif |
|---------|-------|--------|-------|----------|
| S1 | LinkedIn | Post | ... | Awareness |

Retourne les deux documents séparés par `---SPLIT---`.""",
        dod=[
            "gtm-strategy.md présent avec positionnement + ICP",
            "content-calendar.md présent avec au moins 4 entrées",
        ],
    ),
    "content": AgentPlaybook(
        pole="comms",
        files=["comms/messaging-brief.md"],
        description="Brief messaging et ton éditorial",
        template="""Génère un **brief messaging** pour le projet {title}.

# Brief Messaging — {title}
## Promesse principale
## Ton éditorial
## Mots interdits / à éviter
## Exemples de formulations validées
## Règles par canal
| Canal | Longueur | Ton | Format |
|-------|----------|-----|--------|""",
        dod=[
            "messaging-brief.md présent",
            "Promesse principale définie",
            "Règles par canal listées",
        ],
    ),
}
