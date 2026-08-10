"""Robotics ship playbook overrides — BOM + firmware release."""

from __future__ import annotations

from services.rnd_dispatch_playbook_types import AgentPlaybook

PLAYBOOKS: dict[str, AgentPlaybook] = {
    "hardware": AgentPlaybook(
        pole="hardware",
        files=["hardware/release-bom-signoff.md"],
        description="Sign-off BOM release — composants, coût, fournisseurs",
        template="""Génère un **sign-off BOM** pour {title}.

# Release BOM — {title}
## BOM v1 figée (composant · ref · qty · coût)
## Fournisseurs validés / lead time
## Risques supply chain
## Certifications / conformité cibles
## Go / No-Go hardware CEO""",
        dod=["release-bom-signoff.md", "BOM tabulaire", "Risques supply"],
    ),
    "embedded_dev": AgentPlaybook(
        pole="hardware",
        files=["hardware/firmware-release-brief.md"],
        description="Brief release firmware — version, flash, rollback",
        template="""Génère un **brief release firmware** pour {title}.

# Firmware Release — {title}
## Version semver + changelog
## Procédure flash / OTA
## Tests HIL passés
## Plan rollback
## Dépendances capteurs/drivers""",
        dod=["firmware-release-brief.md", "Procédure flash", "Rollback"],
    ),
    "qa": AgentPlaybook(
        pole="hardware",
        files=["hardware/qa-ship-plan.md"],
        description="Plan QA ship robotique — bench, sécurité, endurance",
        template="""Génère un **plan QA ship robotique** pour {title}.

# QA Ship Robotics — {title}
## Tests bench (mouvement, capteurs)
## Sécurité mécanique / électrique
## Endurance 24h
## Seuils ECART release""",
        dod=["qa-ship-plan.md", "Tests sécurité listés"],
    ),
}
