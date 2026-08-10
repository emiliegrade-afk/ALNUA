"""Finance playbooks — accounting."""

from __future__ import annotations

from services.rnd_dispatch_playbook_types import AgentPlaybook

PLAYBOOKS: dict[str, AgentPlaybook] = {
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
}
