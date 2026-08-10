"""App playbooks — dev_app, dev_backend."""

from __future__ import annotations

from services.rnd_dispatch_playbook_types import AgentPlaybook

PLAYBOOKS: dict[str, AgentPlaybook] = {
    "dev_app": AgentPlaybook(
        pole="app",
        files=["app/repo-init.md", "app/mvp-sprint-1-scope.md"],
        description="Setup repo + scope sprint 1 Next.js — scaffold minimal généré automatiquement",
        template="""Génère deux documents pour initialiser le projet frontend {title}.

## Document 1 : repo-init.md
# Repo Init — {title}
## Stack
- Framework : Next.js 14 App Router + TypeScript
- UI : Tailwind CSS + shadcn/ui
- API : Hub ALNUA (FastAPI, HUB_API_URL)
- DB client : Supabase JS

## Structure dossiers
```
web/src/
  app/           — routes Next.js App Router
  components/    — composants réutilisables
  hooks/         — hooks custom
  lib/           — clients API, utils
```

## Variables d'environnement requises
```
NEXT_PUBLIC_HUB_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

## Setup (si GITHUB_TOKEN défini → coding_agent peut initialiser le repo)
```bash
npx create-next-app@latest {title} --typescript --tailwind --app
cd {title} && npx shadcn-ui@latest init
```

---
## Document 2 : mvp-sprint-1-scope.md
# Scope Sprint 1 — {title}
## Objectif du sprint
[1 phrase — ce que l'utilisateur peut faire à la fin du sprint]

## Pages à livrer
| Route | Composant principal | Priorité |
|-------|---------------------|----------|
| / | HomePage | P0 |
| /... | ... | P0 |

## Composants P0
- `components/...` — description

## API calls sprint 1
| Endpoint Hub | Méthode | Usage |
|--------------|---------|-------|
| /... | GET | ... |

## Critères de done sprint 1
- [ ] Pages P0 rendues sans erreur
- [ ] API Hub connectée
- [ ] Déployable sur Vercel

Retourne les deux documents séparés par `---SPLIT---`.""",
        dod=[
            "repo-init.md présent avec stack + structure + setup",
            "mvp-sprint-1-scope.md présent avec pages P0 + critères de done",
            "app/scaffold/ créé avec README.md + package.json + .gitignore",
        ],
    ),
    "dev_backend": AgentPlaybook(
        pole="app",
        files=["app/api-brief.md"],
        description="Brief API FastAPI — endpoints, schemas, migrations",
        template="""Génère un **brief API backend** pour le projet {title}.

# Brief API Backend — {title}
## Endpoints à créer
| Method | Path | Agent | Auth |
|--------|------|-------|------|
| POST | /... | ... | HUB_API_KEY |

## Schemas Pydantic (api/schemas.py)
## Tables Supabase / migrations
## Dépendances Python à ajouter
## Points de vigilance sécurité/performance""",
        dod=[
            "api-brief.md présent",
            "Table endpoints complète",
            "Schemas identifiés",
        ],
    ),
}
