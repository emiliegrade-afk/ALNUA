"""Constants and type aliases for bureau library."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

Timing = Literal["now", "later"]
BureauId = Literal[
    "hub",
    "secretary",
    "app",
    "gaming",
    "robo",
    "marketing",
    "rd",
    "finances",
    "analytics",
    "academy",
]

ROOT = Path(__file__).resolve().parent.parent
LIBRARY_FILE = ROOT / "data" / "bureau_library.json"

BUREAU_LABELS: dict[str, str] = {
    "hub": "Direction",
    "secretary": "Secrétariat",
    "app": "App Dev",
    "gaming": "Gaming Studio",
    "robo": "Robotics Lab",
    "marketing": "Marketing & Contenu",
    "rd": "R&D Lab",
    "finances": "Finance",
    "analytics": "Analytics",
    "academy": "Academy",
}

AGENT_TO_BUREAU: dict[str, str] = {
    "coo": "hub",
    "spec": "hub",
    "qa": "hub",
    "pm": "hub",
    "secretary": "secretary",
    "dev_app": "app",
    "dev_frontend": "app",
    "dev_backend": "app",
    "dev_integrator": "app",
    "dev_gaming": "gaming",
    "content_app": "app",
    "content_gaming": "gaming",
    "content_robo": "robo",
    "content_company": "hub",
    "ads": "hub",
    "content": "marketing",
    "game_director": "gaming",
    "level_designer": "gaming",
    "brainstorm": "rd",
    "rnd_agent": "rd",
    "marketing": "marketing",
    "marketing_agent": "marketing",
    "content_agent": "marketing",
    "hardware": "robo",
    "hardware_agent": "robo",
    "embedded_dev": "robo",
    "accounting": "finances",
    "accountant_agent": "finances",
    "controller": "finances",
    "analyst_business": "analytics",
    "analyst_data": "analytics",
}

VALID_BUREAUS = frozenset(BUREAU_LABELS)

DEFAULT_AGENT_BY_BUREAU: dict[str, str] = {
    "hub": "coo",
    "secretary": "secretary",
    "app": "content_app",
    "gaming": "content_gaming",
    "robo": "content_robo",
    "marketing": "marketing",
    "rd": "rnd_agent",
    "finances": "accounting",
    "analytics": "analyst_business",
    "academy": "dev_app",
}
