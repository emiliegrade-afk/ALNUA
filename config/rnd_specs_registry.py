"""R&D pipeline operating specs — façade (merge by pipeline stage)."""

from __future__ import annotations

from config.agent_operating_spec import AgentOperatingSpec
from config.rnd_specs_center import SPECS as _CENTER
from config.rnd_specs_committee import SPECS as _COMMITTEE
from config.rnd_specs_dossier import SPECS as _DOSSIER
from config.rnd_specs_social import SPECS as _SOCIAL

RND_OPERATING_SPECS: dict[str, AgentOperatingSpec] = {}
RND_OPERATING_SPECS.update(_CENTER)
RND_OPERATING_SPECS.update(_DOSSIER)
RND_OPERATING_SPECS.update(_COMMITTEE)
RND_OPERATING_SPECS.update(_SOCIAL)

_rnd = RND_OPERATING_SPECS


def _add(spec: AgentOperatingSpec) -> None:
    """Compat — prefer stage modules for new specs."""
    _rnd[spec.agent_id] = spec
