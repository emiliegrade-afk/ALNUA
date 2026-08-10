"""Hub-internal playbook overrides — repo ALNUA_HUB, not external product scaffolds."""

from __future__ import annotations

from services.rnd_dispatch_playbook_types import AgentPlaybook

PLAYBOOKS: dict[str, AgentPlaybook] = {
    "spec": AgentPlaybook(
        pole="hub",
        files=["hub/spec-cursor-prompt.md"],
        description="Spec Cursor pour ALNUA_HUB — fichiers api/ web/ services/",
        template="""Génère un **prompt Cursor** pour implémenter cette amélioration **dans ALNUA_HUB** (infra interne).

# Spec Hub — {title}

## Contexte entreprise
[Pourquoi ALNUA a besoin de cette capacité — pas un produit marché externe]

## Repo cible
- **Uniquement** `C:/Dev/ALUNA_HUB` (FastAPI + Next.js web/)
- **Ne pas** modifier nomad, naia, wyrdheim

## Fichiers à créer ou modifier
- `api/routers/...` ou `services/...` ou `web/src/...`

## Étapes d'implémentation
1. ...

## Tests
```bash
pytest tests/ -q -x
```

## Critères d'acceptation
- [ ] Tests passent
- [ ] Pas de régression pipeline agents
- [ ] UI cohérente avec le Hub existant""",
        dod=[
            "spec-cursor-prompt.md dans hub/",
            "Mention explicite ALNUA_HUB",
            "Au moins 3 critères d'acceptation",
        ],
    ),
    "pm": AgentPlaybook(
        pole="hub",
        files=["hub/backlog-infra.md", "hub/acceptance-criteria.md"],
        description="Backlog infra Hub + critères done",
        template="""Génère deux documents pour l'amélioration Hub **{title}** :

## Document 1 : backlog-infra.md
# Backlog Infra Hub — {title}
## User stories P0 (Emilie / agents)
| # | Story | Agent | Effort |
|---|-------|-------|--------|

## Hors périmètre v1
- ...

---
## Document 2 : acceptance-criteria.md
# Critères done — {title}
- [ ] API testée
- [ ] UI si applicable
- [ ] Pas d'impact produits externes

Retourne les deux documents séparés par `---SPLIT---`.""",
        dod=["backlog-infra.md", "acceptance-criteria.md"],
    ),
    "dev_backend": AgentPlaybook(
        pole="hub",
        files=["hub/api-implementation-brief.md"],
        description="Brief API FastAPI dans ALNUA_HUB",
        template="""Génère un **brief d'implémentation backend** pour {title} dans ALNUA_HUB.

# Brief API Hub — {title}
## Endpoints
| Method | Path | Description |
|--------|------|-------------|

## Services (`services/`)
## Schémas Pydantic (`api/schemas.py` ou router)
## Tests pytest à ajouter
## Issue GitHub suggérée
- Repo: ALNUA_HUB, label: agent-ready, slug: hub""",
        dod=["api-implementation-brief.md", "Endpoints listés"],
    ),
    "dev_app": AgentPlaybook(
        pole="hub",
        files=["hub/ui-implementation-brief.md"],
        description="Brief UI Next.js dans web/src/",
        template="""Génère un **brief UI Hub** pour {title}.

# Brief UI Hub — {title}
## Pages / routes (`web/src/app/`)
## Composants (`web/src/components/`)
## Client API (`web/src/lib/`)
## États loading / error
## Critères UX Emilie (CEO)

> Repo: ALNUA_HUB/web/ — pas create-next-app externe.""",
        dod=["ui-implementation-brief.md", "Routes listées"],
    ),
    "qa": AgentPlaybook(
        pole="hub",
        files=["hub/qa-plan.md"],
        description="Plan QA non-régression Hub",
        template="""Génère un **plan QA** pour {title} sur ALNUA_HUB.

# Plan QA Hub — {title}
## Tests automatisés
## Smoke tests manuels
## Régression agents / pipeline
## Seuils de blocage (ECART)""",
        dod=["qa-plan.md", "Smoke tests listés"],
    ),
}
