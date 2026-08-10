"""R&D CEO agent — shared errors, eligibility rules, dispatch priority helpers."""
from __future__ import annotations

from typing import Any

from services.rnd_schemas import RndDossierOut

PACKAGE_ELIGIBLE_STATUSES = frozenset({
    "partial_validated",
    "ready_for_ceo",
    "ceo_approved",
    "ceo_rejected",
    "in_conception",
})


def ceo_package_eligible(dossier: RndDossierOut) -> bool:
    """Package CEO si comité terminé (CR) ou statut pipeline avancé."""
    if dossier.status in PACKAGE_ELIGIBLE_STATUSES:
        return True
    cr = (dossier.committee_report_md or "").strip()
    return len(cr) >= 40


COMMITTEE_REPORT_TEMPLATE = """Rédige un **compte-rendu de clôture comité R&D** markdown pour Emilie (CEO).
Ne résume PAS à l'excès : chaque sujet abordé en réunion doit apparaître.

## Synthèse chronologique des échanges
[Reprendre TOUS les sujets : coûts, pricing, MVP, objections, arbitrages, questions Emilie]

## Chiffres & hypothèses évoqués en réunion
| Élément | Valeur / hypothèse | Source (qui) |
|---------|-------------------|--------------|

## Amendements & demandes Emilie
[Liste à puces — reformulations, réductions coût, périmètre, priorités]

## Décisions actées
[Liste à puces — ce qui a été tranché]

## Sections validées / à revoir
| Section | Statut | Commentaire comité |
|---------|--------|-------------------|

## Actions ouvertes
- [ ] ...

## Risques ouverts
- ...

## Recommandation GO / MAYBE / NO pour le CEO
**Verdict :** GO|MAYBE|NO
[2-4 phrases factuelles]

---
*CR généré automatiquement — ALNUA Hub R&D*
"""


class CeoPackageNotReadyError(ValueError):
    """Dossier not ready for CEO package generation."""


class CeoDecisionError(ValueError):
    """Invalid CEO decision state."""


class DispatchNotAllowedError(ValueError):
    """Dispatch blocked — CEO approval required."""


_PRIORITY_TEXT_TO_INT = {
    "critical": 9,
    "high": 7,
    "medium": 5,
    "low": 2,
}


def normalize_priority_label(label: str) -> str:
    """Map unknown roadmap priority labels to medium."""
    return label if label in _PRIORITY_TEXT_TO_INT else "medium"


def roadmap_priority_values(label: str) -> list[Any]:
    """Support text (v2) and integer (legacy) roadmap.priority columns."""
    text = normalize_priority_label(label)
    return [text, _PRIORITY_TEXT_TO_INT[text]]
