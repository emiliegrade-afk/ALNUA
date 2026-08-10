"""Agent tier registry, aliases, and tier defaults."""
from __future__ import annotations

_AGENT_DISPLAY_FALLBACKS: dict[str, dict[str, str]] = {
    "rnd_dossier": {
        "display_name": "Pipeline R&D",
        "role_label": "Assemblage dossier",
        "department": "Pôle Innovation",
        "room": "rnd_lab",
    },
    "rnd_ceo": {
        "display_name": "Package CEO",
        "role_label": "Dossier → validation Emilie",
        "department": "Pôle Innovation",
        "room": "rnd_lab",
    },
    "rnd_committee": {
        "display_name": "Comité R&D",
        "role_label": "Revue comité",
        "department": "Pôle Innovation",
        "room": "rnd_lab",
    },
    "rnd_social": {
        "display_name": "Social R&D",
        "role_label": "Stratégie sociale dossier",
        "department": "Hub Business",
        "room": "comms_hub",
    },
    "rnd_visual": {
        "display_name": "Identité visuelle",
        "role_label": "Moodboard & brand dossier",
        "department": "Hub Business",
        "room": "comms_hub",
    },
    "rnd_product": {
        "display_name": "Fiche produit",
        "role_label": "Packaging produit R&D",
        "department": "Pôle App",
        "room": "app_office",
    },
}

# Alias runtime → clé canonique (UI / agent_models.json)
AGENT_ID_ALIASES: dict[str, str] = {
    "coo_agent": "coo",
    "spec_agent": "spec",
    "pm_agent": "pm",
    "qa_agent": "qa",
    "content_agent": "content",
    "brainstorm_agent": "brainstorm",
    "hardware_agent": "hardware",
    "marketing_agent": "marketing",
    "dev_app_agent": "dev_app",
    "dev_frontend_agent": "dev_frontend",
    "dev_integrator_agent": "dev_integrator",
    "content_app_agent": "content_app",
    "content_gaming_agent": "content_gaming",
    "content_robo_agent": "content_robo",
    "content_company_agent": "content_company",
    "ads_agent": "ads",
    "dev_gaming_agent": "dev_gaming",
    "embedded_dev_agent": "embedded_dev",
    "game_director_agent": "game_director",
    "game_dir": "game_director",
    "dev_game": "dev_gaming",
    "rnd_center": "rnd_agent",
    "rnd_agent_agent": "rnd_agent",
    "rnd_ceo_agent": "rnd_ceo",
    "rnd_dossier_agent": "rnd_dossier",
    "rnd_committee_agent": "rnd_committee",
    "rnd_social_agent": "rnd_social",
    "rnd_visual_agent": "rnd_visual",
    "rnd_product_agent": "rnd_product",
    "embedded": "embedded_dev",
    "secretary_agent": "secretary",
    "admin_agent": "secretary",
    "dev_backend_agent": "dev_backend",
    "backend_agent": "dev_backend",
    "level_designer_agent": "level_designer",
    "controller_agent": "controller",
    "financial_controller": "controller",
    "analyst_business_agent": "analyst_business",
    "business_analyst": "analyst_business",
    "analyst_data_agent": "analyst_data",
    "data_analyst": "analyst_data",
    # Studio Gaming — 7 rôles spécialisés (Phase 13, ROADMAP.md)
    "ai_programmer_agent": "ai_programmer",
    "environment_artist_agent": "environment_artist",
    "technical_artist_agent": "technical_artist",
    "narrative_designer_agent": "narrative_designer",
    "vfx_artist_agent": "vfx_artist",
    "sound_designer_agent": "sound_designer",
    "qa_gaming_agent": "qa_gaming",
    # Atelier Robo — 8 rôles spécialisés (Phase 13, ROADMAP.md)
    "vision_ai_agent": "vision_ai",
    "electronics_agent": "electronics",
    "firmware_agent": "firmware",
    "mechanical_agent": "mechanical",
    "industrial_design_agent": "industrial_design",
    "qa_robot_agent": "qa_robot",
    "safety_agent": "safety",
    "simulation_agent": "simulation",
}

# Tier par défaut pour chaque agent (mode AUTO)
AGENT_TIERS: dict[str, str] = {
    "coo":           "premium",
    "spec":          "premium",
    "brainstorm":    "premium",
    "game_director": "premium",
    "rnd_agent":     "premium",
    "qa":            "standard",
    "dev_app":       "standard",
    "dev_frontend":  "standard",
    "dev_integrator": "standard",
    "content_app":    "standard",
    "content_gaming": "standard",
    "content_robo":   "standard",
    "content_company": "standard",
    "ads":           "standard",
    "coding_coach":  "fast",
    "dev_gaming":    "standard",
    "marketing":     "standard",
    "hardware":      "standard",
    "embedded_dev":  "standard",
    "content":       "standard",
    "pm":               "fast",
    "accounting":       "fast",
    "secretary":        "fast",
    "controller":       "fast",
    "dev_backend":      "standard",
    "level_designer":   "standard",
    "analyst_business": "standard",
    "analyst_data":     "standard",
    "rnd_dossier":      "premium",
    "rnd_ceo":          "premium",
    "rnd_committee":    "premium",
    "rnd_social":       "standard",
    "rnd_visual":       "standard",
    "rnd_product":      "standard",
    # Studio Gaming — 7 rôles spécialisés (Phase 13, ROADMAP.md)
    "ai_programmer":      "standard",
    "environment_artist": "standard",
    "technical_artist":   "standard",
    "narrative_designer": "standard",
    "vfx_artist":         "standard",
    "sound_designer":     "standard",
    "qa_gaming":          "standard",
    # Atelier Robo — 8 rôles spécialisés (Phase 13, ROADMAP.md)
    "vision_ai":          "standard",
    "electronics":        "standard",
    "firmware":           "standard",
    "mechanical":         "standard",
    "industrial_design":  "standard",
    "qa_robot":           "standard",
    "safety":             "standard",
    "simulation":         "standard",
}

# Agents whose Paramètres model also drives the autonomous coding pipeline (Hub Agent / Aider).
CODING_AGENT_IDS: frozenset[str] = frozenset(
    {
        "dev_app",
        "dev_backend",
        "dev_gaming",
        "embedded_dev",
        "dev_frontend",
        "dev_integrator",
        "ads",
        # DEC-020 — Gaming specialists may run Claude Code on UE_PROJECT_PATH
        "ai_programmer",
        "technical_artist",
        "vfx_artist",
    }
)

# Modèle par défaut par tier
TIER_DEFAULTS: dict[str, str] = {
    "premium":  "anthropic/claude-sonnet-4",
    "standard": "deepseek/deepseek-chat-v3.1",
    "fast":     "anthropic/claude-haiku-4-5",
}

# Alias historique — services/llm_router.py
TIER_MODELS: dict[str, str] = TIER_DEFAULTS

# Noms d'affichage CrewAI / retry loop → clé Mem0 canonique
MEMORY_DISPLAY_ALIASES: dict[str, str] = {
    "devapp": "dev_app",
    "devgaming": "dev_gaming",
    "embeddeddev": "embedded_dev",
}


def agent_display(agent_id: str) -> dict[str, str]:
    from config.agent_personas import ROOMS, get_persona

    persona = get_persona(agent_id)
    if persona:
        room_id = persona.get("room", "")
        department = ROOMS.get(room_id, {}).get("label", room_id or "ALNUA")
        return {
            "display_name": f"{persona['first_name']} {persona['last_name']}",
            "role_label": persona.get("role_label", agent_id),
            "department": department,
            "room": room_id,
        }
    fb = _AGENT_DISPLAY_FALLBACKS.get(agent_id)
    if fb:
        return fb
    return {
        "display_name": agent_id,
        "role_label": agent_id,
        "department": "ALNUA",
        "room": "",
    }


def normalize_agent_id(agent_id: str) -> str:
    """Mappe coo_agent, spec_agent, etc. vers les clés de AGENT_TIERS."""
    key = agent_id.strip().lower()
    if key in AGENT_ID_ALIASES:
        return AGENT_ID_ALIASES[key]
    if key in AGENT_TIERS:
        return key
    if key.endswith("_agent"):
        short = key.removesuffix("_agent")
        if short in AGENT_TIERS:
            return short
    return key


def memory_agent_id(agent_id: str) -> str:
    """Clé canonique Mem0 — alignée sur Paramètres / agent_models.json."""
    compact = agent_id.strip().lower().replace(" ", "").replace("-", "")
    if compact in MEMORY_DISPLAY_ALIASES:
        return MEMORY_DISPLAY_ALIASES[compact]
    return normalize_agent_id(agent_id)
