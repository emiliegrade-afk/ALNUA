"""Gaming playbooks — dev_gaming, game_director."""

from __future__ import annotations

from services.rnd_dispatch_playbook_types import AgentPlaybook

PLAYBOOKS: dict[str, AgentPlaybook] = {
    "dev_gaming": AgentPlaybook(
        pole="gaming",
        files=["gaming/dev-gaming-brief.md"],
        description="Brief dev Godot 4 — scènes, systèmes, GDScript",
        template="""Génère un **brief de développement Godot 4** pour le projet {title}.

# Brief Dev Gaming — {title}
## Scènes à créer
| Scène | Node root | Description |
|-------|-----------|-------------|

## Systèmes Godot
## Scripts GDScript principaux
## Ressources (assets nécessaires)
## Intégrations Hub (signaux → API)
## Points de vigilance performance Godot""",
        dod=[
            "dev-gaming-brief.md présent",
            "Liste scènes + scripts",
        ],
    ),
    "game_director": AgentPlaybook(
        pole="gaming",
        files=["gaming/gdd-extract.md"],
        description="Extrait GDD — vision gameplay, boucle de jeu, méchaniques core",
        template="""Génère un **extrait GDD de conception** pour le projet {title}.

# GDD Extrait — {title}
## Vision & pitch (1 phrase)
## Boucle de jeu (game loop)
## Mécaniques core
| Mécanique | Description | Priorité |
|-----------|-------------|----------|

## Flux joueur (onboarding → progression → rétention)
## Inspirations ludiques
## Risques conception""",
        dod=[
            "gdd-extract.md présent",
            "Boucle de jeu définie",
            "Mécaniques core listées",
        ],
    ),
}
