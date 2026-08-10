"""Direction playbooks — spec, pm, coo."""

from __future__ import annotations

from services.rnd_dispatch_playbook_types import AgentPlaybook

PLAYBOOKS: dict[str, AgentPlaybook] = {
    "spec": AgentPlaybook(
        pole="direction",
        files=["direction/spec-cursor-prompt.md"],
        description="Prompt Cursor complet prêt à coller dans Composer",
        template="""Génère un **prompt Cursor complet** (markdown) pour implémenter ce projet.

Structure OBLIGATOIRE :
# Spec — {title}

## Contexte
[Problème / besoin en 3-5 phrases]

## Fichiers à créer ou modifier
- `chemin/fichier.ext` — raison

## Étapes d'implémentation
1. [Étape concrète avec code si nécessaire]
2. ...

## Stack ciblé
- Backend : FastAPI (api/routers/)
- Frontend : Next.js 14 (web/src/)
- DB : Supabase
- Agents : agents/{agent_name}.py

## Tests & validation
```bash
# commandes de test
```

## Critères d'acceptation
- [ ] critère mesurable
- [ ] critère mesurable

Sois exhaustif — ce prompt sera exécuté directement par Cursor sans intervention humaine.""",
        dod=[
            "Fichier spec-cursor-prompt.md présent dans direction/",
            "Prompt contient les sections Contexte, Fichiers, Étapes, Stack, Tests, Critères",
            "Au moins 3 critères d'acceptation listés",
        ],
    ),
    "pm": AgentPlaybook(
        pole="direction",
        files=["direction/backlog-mvp.md", "direction/acceptance-criteria-v1.md"],
        description="Backlog MVP priorisé + critères d'acceptation v1",
        template="""Génère deux documents distincts pour le projet {title} :

## Document 1 : backlog-mvp.md
Format :
# Backlog MVP — {title}
## Épiques
| # | Épique | Priorité | Agents | Effort |
|---|--------|----------|--------|--------|
| 1 | ... | P0 | dev_app | S |

## User Stories P0
- [ ] En tant que [persona], je veux [action] pour [bénéfice]

## User Stories P1
...

## User Stories P2
...

---
## Document 2 : acceptance-criteria-v1.md
Format :
# Critères d'acceptation v1 — {title}
## Fonctionnel
- [ ] ...
## Performance
- [ ] ...
## Sécurité
- [ ] ...

Retourne les deux documents séparés par `---SPLIT---`.""",
        dod=[
            "backlog-mvp.md présent avec au moins 3 user stories",
            "acceptance-criteria-v1.md présent avec critères fonctionnels",
            "Priorisation P0/P1/P2 explicite",
        ],
    ),
    "coo": AgentPlaybook(
        pole="direction",
        files=["direction/coo-coordination-brief.md"],
        description="Brief coordination COO — arbitrages, dépendances inter-pôles, timeline",
        template="""Génère un **brief de coordination COO** pour lancer la conception du projet {title}.

# Brief COO — {title}

## Objectif de la phase conception
[1 paragraphe — ce qu'on valide en conception]

## Pôles impliqués & séquence
| Pôle | Agent | Livrable attendu | Délai |
|------|-------|-----------------|-------|
| direction | spec | spec-cursor-prompt.md | J+1 |
| ... | ... | ... | ... |

## Dépendances critiques
[Quels livrables débloquent quels autres]

## Points d'arbitrage ouverts
- [ ] [décision à trancher]

## Signal de succès (fin conception)
[Quand considère-t-on la phase conception terminée]

Sois concret — ceci est le brief opérationnel, pas un document stratégique.""",
        dod=[
            "coo-coordination-brief.md présent",
            "Tableau pôles/agents/livrables rempli",
            "Au moins 1 point d'arbitrage identifié",
        ],
    ),
}
