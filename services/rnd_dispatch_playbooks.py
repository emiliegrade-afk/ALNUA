"""Playbooks de livraison par agent — Phase 9 Workspace Dispatch.

Chaque playbook définit :
- pole       : sous-dossier workspace cible
- files      : chemins relatifs au projet (ex: "direction/spec-cursor-prompt.md")
- template   : template markdown avec sections obligatoires
- dod        : checklist Definition of Done (validation humaine)
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Playbook type hint
# ---------------------------------------------------------------------------

class AgentPlaybook:
    """Playbook immutable pour un agent dispatch."""

    def __init__(
        self,
        pole: str,
        files: list[str],
        description: str,
        template: str,
        dod: list[str],
    ) -> None:
        self.pole = pole
        self.files = files  # chemins relatifs au projet root
        self.description = description
        self.template = template  # prompt instructions pour le LLM
        self.dod = dod

    def primary_file(self) -> str:
        return self.files[0] if self.files else ""

    def pole_relative_filename(self, idx: int = 0) -> str:
        """Ex: 'direction/spec-cursor-prompt.md' → 'spec-cursor-prompt.md'"""
        f = self.files[idx] if idx < len(self.files) else self.primary_file()
        return f.split("/", 1)[-1] if "/" in f else f


# ---------------------------------------------------------------------------
# Playbooks registry
# ---------------------------------------------------------------------------

_PLAYBOOKS: dict[str, AgentPlaybook] = {
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

    "accounting": AgentPlaybook(
        pole="finance",
        files=["finance/business-case.md"],
        description="Business case financier structuré avec hypothèses CEO",
        template="""Génère un **business case financier** pour le projet {title}.

# Business Case — {title}
## Résumé exécutif
## Hypothèses de revenus
| Source | Année 1 | Année 2 | Année 3 |
|--------|---------|---------|---------|

## Structure de coûts
| Catégorie | Mensuel | Annuel |
|-----------|---------|--------|

## Seuil de rentabilité
## Scénarios (pessimiste / réaliste / optimiste)
## Recommandation financière
## Alertes et risques financiers""",
        dod=[
            "business-case.md présent",
            "Tableau revenus sur 3 ans",
            "Seuil de rentabilité calculé",
            "Au moins 2 scénarios chiffrés",
        ],
    ),

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

    "brainstorm": AgentPlaybook(
        pole="innovation",
        files=["innovation/ideation-brief.md"],
        description="Brief idéation — angles non-évidents, hypothèses à tester",
        template="""Génère un **brief d'idéation R&D** pour le projet {title}.

# Idéation R&D — {title}
## Angles non-évidents (hors consensus)
1. ...
## Hypothèses à valider (ordre de priorité)
| Hypothèse | Impact si validée | Comment tester |
|-----------|------------------|----------------|

## Technologies émergentes pertinentes
## Risques d'innovation
## Signal faibles à surveiller""",
        dod=[
            "ideation-brief.md présent",
            "Au moins 3 angles non-évidents",
            "Hypothèses avec méthode de test",
        ],
    ),

    "rnd_agent": AgentPlaybook(
        pole="innovation",
        files=["innovation/research-report.md"],
        description="Rapport de recherche — état de l'art, benchmarks, recommandations",
        template="""Génère un **rapport de recherche** pour le projet {title}.

# Rapport Recherche — {title}
## État de l'art
## Benchmarks concurrents
| Solution | Forces | Faiblesses | Pertinence |
|----------|--------|------------|------------|

## Technologies recommandées (avec justification)
## Risques techniques identifiés
## Ressources clés (docs, papiers, repos)
## Recommandation finale""",
        dod=[
            "research-report.md présent",
            "Benchmark avec au moins 3 solutions analysées",
            "Recommandation finale claire",
        ],
    ),

    "hardware": AgentPlaybook(
        pole="hardware",
        files=["hardware/hardware-brief.md"],
        description="Brief hardware — composants, contraintes, BOM estimatif",
        template="""Génère un **brief hardware** pour le projet {title}.

# Brief Hardware — {title}
## Contraintes matérielles
## BOM estimatif (Bill of Materials)
| Composant | Quantité | Coût unit. | Fournisseur |
|-----------|----------|------------|-------------|

## Architecture système
## Protocoles de communication
## Risques hardware
## Points de vigilance réglementation""",
        dod=[
            "hardware-brief.md présent",
            "BOM avec au moins 3 composants",
        ],
    ),

    "embedded_dev": AgentPlaybook(
        pole="hardware",
        files=["hardware/embedded-brief.md"],
        description="Brief embedded — firmware, protocoles, drivers",
        template="""Génère un **brief embedded** pour le projet {title}.

# Brief Embedded — {title}
## Architecture firmware
## Protocoles (I2C / SPI / UART / BLE / WiFi)
## Stack logicielle (RTOS, HAL, libs)
## Modules à développer
| Module | Description | Priorité |
|--------|-------------|----------|

## Tests hardware-in-the-loop
## Contraintes temps réel""",
        dod=[
            "embedded-brief.md présent",
            "Protocoles identifiés",
            "Modules listés",
        ],
    ),

    "analyst_business": AgentPlaybook(
        pole="analytics",
        files=["analytics/business-analysis.md"],
        description="Analyse business — TAM/SAM/SOM, KPIs, modèle de croissance",
        template="""Génère une **analyse business** pour le projet {title}.

# Analyse Business — {title}
## TAM / SAM / SOM
## KPIs de succès
| KPI | Cible J+30 | Cible J+90 | Cible J+365 |
|-----|-----------|-----------|------------|

## Modèle de croissance
## Risques business (top 3)
## Opportunités adjacentes
## Décision recommandée (GO / PIVOT / STOP)""",
        dod=[
            "business-analysis.md présent",
            "TAM/SAM/SOM chiffrés",
            "KPIs avec targets temporels",
        ],
    ),

    "analyst_data": AgentPlaybook(
        pole="analytics",
        files=["analytics/data-brief.md"],
        description="Brief données — schéma tracking, dashboard metrics, pipeline",
        template="""Génère un **brief données** pour le projet {title}.

# Brief Données — {title}
## Événements à tracker
| Événement | Propriétés | Outil |
|-----------|-----------|-------|

## Schéma Supabase / tables analytics
## Dashboard (métriques à afficher)
## Pipeline de données
## Alertes et seuils critiques""",
        dod=[
            "data-brief.md présent",
            "Événements tracking listés",
            "Dashboard défini",
        ],
    ),
}


def get_playbook(agent_id: str) -> AgentPlaybook | None:
    """Retourne le playbook pour un agent_id normalisé, ou None si inconnu."""
    return _PLAYBOOKS.get(agent_id)


def all_required_files(agent_ids: list[str]) -> list[str]:
    """Agrège tous les fichiers requis pour un set d'agents dispatch."""
    files: list[str] = []
    seen: set[str] = set()
    for aid in agent_ids:
        pb = get_playbook(aid)
        if pb:
            for f in pb.files:
                if f not in seen:
                    files.append(f)
                    seen.add(f)
    return files


def _file_full_path(workspace_path: str, slug: str, f: str) -> str:
    """Option A : 'direction/spec.md' -> '{ws}/direction/{slug}/spec.md'"""
    if "/" in f:
        pole, filename = f.split("/", 1)
        return f"{workspace_path}/{pole}/{slug}/{filename}"
    return f"{workspace_path}/{slug}/{f}"


def build_instruction_with_paths(
    agent_id: str,
    dossier_title: str,
    slug: str,
    workspace_path: str,
    context_excerpt: str,
    extra: dict[str, Any] | None = None,
) -> str:
    """Construit l'instruction enrichie avec paths workspace pour un agent dispatch.

    Convention Option A : ALNUA/{pole}/{slug}/{filename}
    Les fichiers dans pb.files sont au format 'pole/filename'.
    """
    pb = get_playbook(agent_id)
    if not pb:
        # Fallback générique
        return (
            f"Projet ALNUA : {dossier_title}\n\n"
            f"Workspace : {workspace_path}/\n\n"
            f"Contexte :\n{context_excerpt}\n\n"
            "Produis un livrable markdown structuré et actionnable."
        )

    files_str = "\n".join(
        f"  - {_file_full_path(workspace_path, slug, f)}"
        for f in pb.files
    )
    template_filled = pb.template.replace("{title}", dossier_title)

    extra_context = ""
    if extra:
        extra_context = "\n\nDonnées contextuelles :\n" + "\n".join(
            f"{k}: {v}" for k, v in extra.items() if v
        )

    return (
        f"Projet ALNUA validé par la CEO : {dossier_title}\n"
        f"Pôle : {pb.pole}\n"
        f"Workspace : {workspace_path}/{pb.pole}/{slug}/\n\n"
        f"FICHIERS À PRODUIRE (écriture automatique sur disque) :\n{files_str}\n\n"
        f"Contexte dossier CEO :\n{context_excerpt}\n"
        f"{extra_context}\n\n"
        f"--- TEMPLATE LIVRABLE ---\n"
        f"{template_filled}"
    )
