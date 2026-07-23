"""Per-user/tenant personality overrides for agent system prompts."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Tone = Literal["formal", "casual", "concise", "detailed", "balanced"]
Vocabulary = Literal["tech-savvy", "beginner-friendly", "business", "creative"]


class PersonalityOverrides(BaseModel):
    tone: Tone = "balanced"
    vocabulary: Vocabulary = "business"
    emoji: bool = False
    response_length: int = Field(default=800, ge=100, le=4000)


_TONE_BLOCKS: dict[Tone, str] = {
    "formal": "Adopte un ton professionnel et structuré. Vouvoiement implicite.",
    "casual": "Ton décontracté et direct, comme un collègue de confiance.",
    "concise": "Réponses courtes et actionnables. Pas de prose inutile.",
    "detailed": "Réponses approfondies avec contexte et nuances.",
    "balanced": "Équilibre entre clarté et concision.",
}

_VOCAB_BLOCKS: dict[Vocabulary, str] = {
    "tech-savvy": "Vocabulaire technique assumé — pas besoin de sur-expliquer.",
    "beginner-friendly": "Explique les concepts techniques simplement.",
    "business": "Orienté décision, ROI, priorités exécutives.",
    "creative": "Langage évocateur, métaphores, storytelling léger.",
}


def build_personality_block(overrides: PersonalityOverrides | None) -> str:
    """Compile personality directives to append to system prompt."""
    if overrides is None:
        return ""

    lines = ["## Personnalisation utilisateur"]
    lines.append(_TONE_BLOCKS.get(overrides.tone, _TONE_BLOCKS["balanced"]))
    lines.append(_VOCAB_BLOCKS.get(overrides.vocabulary, _VOCAB_BLOCKS["business"]))
    if overrides.emoji:
        lines.append("Tu peux utiliser des emojis avec parcimonie.")
    else:
        lines.append("Pas d'emojis sauf demande explicite.")
    lines.append(f"Cible ~{overrides.response_length} caractères par réponse.")
    return "\n".join(lines)


def apply_personality(system_prompt: str, overrides: PersonalityOverrides | None) -> str:
    """Append personality block to an agent system prompt."""
    block = build_personality_block(overrides)
    if not block:
        return system_prompt
    return f"{system_prompt}\n\n{block}"


# In-memory store until Supabase tenants table is migrated
_tenant_personalities: dict[str, PersonalityOverrides] = {}


def get_personality(tenant_id: str) -> PersonalityOverrides | None:
    return _tenant_personalities.get(tenant_id)


def set_personality(tenant_id: str, overrides: PersonalityOverrides) -> None:
    _tenant_personalities[tenant_id] = overrides
