"""Innovation playbooks — brainstorm, rnd_agent."""

from __future__ import annotations

from services.rnd_dispatch_playbook_types import AgentPlaybook

PLAYBOOKS: dict[str, AgentPlaybook] = {
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
}
