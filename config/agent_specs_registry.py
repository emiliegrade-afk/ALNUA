"""Registry of AgentOperatingSpec — façade BUG-004 (merge by pôle)."""
from __future__ import annotations

from config.agent_operating_spec import AgentOperatingSpec
from config.agent_specs_shared import _MEM_HUB, _MEM_IGNORE  # noqa: F401 — re-export

from config.agent_specs_app import SPECS as _APP
from config.agent_specs_comms import SPECS as _COMMS
from config.agent_specs_direction import SPECS as _DIRECTION
from config.agent_specs_finance_analytics import SPECS as _FINANCE
from config.agent_specs_gaming import SPECS as _GAMING
from config.agent_specs_legal import SPECS as _LEGAL
from config.agent_specs_housekeeper import SPECS as _HOUSEKEEPER
from config.agent_specs_rnd_core import SPECS as _RND
from config.agent_specs_robo import SPECS as _ROBO

AGENT_OPERATING_SPECS: dict[str, AgentOperatingSpec] = {}
AGENT_OPERATING_SPECS.update(_DIRECTION)
AGENT_OPERATING_SPECS.update(_LEGAL)
AGENT_OPERATING_SPECS.update(_HOUSEKEEPER)
AGENT_OPERATING_SPECS.update(_APP)
AGENT_OPERATING_SPECS.update(_GAMING)
AGENT_OPERATING_SPECS.update(_RND)
AGENT_OPERATING_SPECS.update(_COMMS)
AGENT_OPERATING_SPECS.update(_FINANCE)
AGENT_OPERATING_SPECS.update(_ROBO)

_specs = AGENT_OPERATING_SPECS


def _add(spec: AgentOperatingSpec) -> None:
    """Compat — prefer pole modules for new specs."""
    _specs[spec.agent_id] = spec
