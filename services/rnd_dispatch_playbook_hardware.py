"""Hardware playbooks — hardware, embedded_dev."""

from __future__ import annotations

from services.rnd_dispatch_playbook_types import AgentPlaybook

PLAYBOOKS: dict[str, AgentPlaybook] = {
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
}
