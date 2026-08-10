"""Gaming ship playbook overrides — Godot release + GDD sign-off."""

from __future__ import annotations

from services.rnd_dispatch_playbook_types import AgentPlaybook

PLAYBOOKS: dict[str, AgentPlaybook] = {
    "game_director": AgentPlaybook(
        pole="gaming",
        files=["gaming/release-gdd-checklist.md"],
        description="Checklist release GDD — core loop, scope build, risques design",
        template="""Génère une **checklist release GDD** pour le jeu {title}.

# Release GDD — {title}
## Core loop validé (oui/non + preuve playtest)
## Scope build vs wishlist (ce qui ship / ce qui wait)
## Mécaniques P0 testées
## Risques design résiduels
## Critères wishlist / early access CEO""",
        dod=["release-gdd-checklist.md", "Core loop mentionné", "Scope build explicite"],
    ),
    "dev_gaming": AgentPlaybook(
        pole="gaming",
        files=["gaming/release-build-checklist.md"],
        description="Checklist build Godot — export, perfs, crash-free",
        template="""Génère une **checklist build Godot 4** pour {title}.

# Release Build — {title}
## Scènes P0 jouables sans crash
## Exports cibles (Windows / mobile / web)
## Budget perfs (FPS, mémoire)
## Tests automatisés / GUT
## Bloquants release listés""",
        dod=["release-build-checklist.md", "Exports listés", "Perfs cibles"],
    ),
    "qa": AgentPlaybook(
        pole="gaming",
        files=["gaming/qa-ship-plan.md"],
        description="Plan QA ship jeu — smoke, régression gameplay",
        template="""Génère un **plan QA ship** pour {title}.

# QA Ship Gaming — {title}
## Smoke tests gameplay (15 min)
## Régression mécaniques core
## Save/load · edge cases
## Seuils ECART release""",
        dod=["qa-ship-plan.md", "Smoke tests listés"],
    ),
}
