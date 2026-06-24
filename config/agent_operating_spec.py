"""
agent_operating_spec.py — Professional agent operating specs (9-layer model).

Layers (order matters):
  1. Mission (raison d'être)
  2. Responsabilités
  3. Hors périmètre
  4. Niveau d'expertise
  5. Processus de raisonnement
  6. Communication (ton, longueur, structure)
  7. Priorités
  8. Mémoire
  9. Personnalité (archetype + traits — last)
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from config.agent_personas import get_display_name

ExpertiseLevel = Literal["assistant", "expert", "consultant"]

_LEVEL_LABELS: dict[ExpertiseLevel, str] = {
    "assistant": "Niveau assistant — réponses ciblées, information de base, exécution guidée",
    "expert": "Niveau expert — analyse approfondie, recommandations détaillées, raisonnement structuré",
    "consultant": "Niveau consultant — vision stratégique, arbitrages, anticipation des risques",
}


class AgentOperatingSpec(BaseModel):
    """Structured operating contract for an ALNUA agent."""

    agent_id: str
    mission: str = Field(..., min_length=10, description="Une seule phrase — raison d'être")
    expertise_level: ExpertiseLevel = "expert"
    expertise_note: str = ""
    responsabilites: list[str] = Field(..., min_length=2)
    hors_perimetre: list[str] = Field(..., min_length=2)
    processus: list[str] = Field(..., min_length=3)
    priorites: list[str] = Field(..., min_length=3)
    ton: list[str] = Field(default_factory=lambda: ["professionnel", "clair", "direct"])
    longueur: str = "moyenne"
    structure: list[str] = Field(
        default_factory=lambda: ["résumé", "analyse", "recommandations ou plan d'action"]
    )
    memoire_conserve: list[str] = Field(default_factory=list)
    memoire_ignore: list[str] = Field(default_factory=list)
    archetype: str = "spécialiste"
    traits: list[str] = Field(..., min_length=2)
    output_format: str = "JSON valide structuré, sauf indication contraire."
    relations: list[str] = Field(default_factory=list)
    extra_sections: dict[str, str] = Field(default_factory=dict)


def compile_system_prompt(spec: AgentOperatingSpec, *, with_identity: bool = True) -> str:
    """Compile spec → system prompt text for LLM."""
    name = get_display_name(spec.agent_id)
    role = spec.agent_id.replace("_", " ")

    lines: list[str] = []
    if with_identity:
        lines.extend([f"Tu es {name}, agent {role} d'ALNUA.", ""])

    lines.extend(
        [
            "## Mission",
            spec.mission.strip(),
            "",
            "## Niveau d'expertise",
            _LEVEL_LABELS[spec.expertise_level],
        ]
    )
    if spec.expertise_note.strip():
        lines.append(spec.expertise_note.strip())

    lines.extend(["", "## Responsabilités"])
    lines.extend(f"- {r}" for r in spec.responsabilites)

    lines.extend(["", "## Hors périmètre"])
    lines.extend(f"- {h}" for h in spec.hors_perimetre)

    lines.extend(["", "## Processus de raisonnement"])
    for i, step in enumerate(spec.processus, 1):
        lines.append(f"{i}. {step}")

    lines.extend(["", "## Priorités (en cas de conflit)"])
    for i, p in enumerate(spec.priorites, 1):
        lines.append(f"{i}. {p}")

    lines.extend(
        [
            "",
            "## Communication",
            f"Ton : {', '.join(spec.ton)}.",
            f"Longueur par défaut : {spec.longueur}.",
            f"Structure : {' → '.join(spec.structure)}.",
        ]
    )

    if spec.memoire_conserve or spec.memoire_ignore:
        lines.append("")
        lines.append("## Mémoire")
        if spec.memoire_conserve:
            lines.append("Conserve (Mem0 / contexte Hub) :")
            lines.extend(f"- {m}" for m in spec.memoire_conserve)
        if spec.memoire_ignore:
            lines.append("Ignore :")
            lines.extend(f"- {m}" for m in spec.memoire_ignore)

    if spec.relations:
        lines.extend(["", "## Relations équipe"])
        lines.extend(f"- {r}" for r in spec.relations)

    for title, body in spec.extra_sections.items():
        lines.extend(["", f"## {title}", body.strip()])

    lines.extend(
        [
            "",
            "## Personnalité (dernière couche)",
            f"Archétype : {spec.archetype}.",
            f"Traits : {', '.join(spec.traits)}.",
            "",
            "## Format de sortie",
            spec.output_format.strip(),
        ]
    )

    return "\n".join(lines)


_REGISTRY: dict[str, AgentOperatingSpec] | None = None


def _load_registry() -> dict[str, AgentOperatingSpec]:
    global _REGISTRY
    if _REGISTRY is None:
        from config.agent_specs_registry import AGENT_OPERATING_SPECS
        from config.rnd_specs_registry import RND_OPERATING_SPECS
        from config.tool_specs_registry import TOOL_OPERATING_SPECS

        _REGISTRY = {**AGENT_OPERATING_SPECS, **RND_OPERATING_SPECS, **TOOL_OPERATING_SPECS}
    return _REGISTRY


def build_committee_system_prompt(member_agent_id: str, dossier_context: str) -> str:
    """Comité R&D : spec agent membre + overlay comité + contexte dossier."""
    base = get_system_prompt(member_agent_id)
    overlay = get_system_prompt("rnd_committee_overlay", with_identity=False)
    ctx = dossier_context.strip()[:6000]
    return f"{base}\n\n---\n\n## Mode comité R&D\n{overlay}\n\n## Contexte dossier\n{ctx}"


def get_operating_spec(agent_id: str) -> AgentOperatingSpec:
    registry = _load_registry()
    key = agent_id.strip().lower()
    if key not in registry:
        raise KeyError(f"No operating spec for agent_id={agent_id!r}")
    return registry[key]


def get_system_prompt(agent_id: str, *, with_identity: bool = True) -> str:
    """Compiled system prompt for an agent or variant key."""
    return compile_system_prompt(get_operating_spec(agent_id), with_identity=with_identity)


def crew_backstory(agent_id: str, _legacy_body: str | None = None) -> str:
    """CrewAI backstory — full operating spec (legacy body arg ignored)."""
    return get_system_prompt(agent_id)


def list_spec_agent_ids() -> list[str]:
    return sorted(_load_registry().keys())
