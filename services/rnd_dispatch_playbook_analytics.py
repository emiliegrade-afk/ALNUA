"""Analytics playbooks — analyst_business, analyst_data."""

from __future__ import annotations

from services.rnd_dispatch_playbook_types import AgentPlaybook

PLAYBOOKS: dict[str, AgentPlaybook] = {
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
