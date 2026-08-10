"""ROOMS and TEAMS maps for ALNUA agents."""
from __future__ import annotations

ROOMS: dict[str, dict] = {
    "direction": {
        "label": "Bureau de Direction",
        "description": "Supervision transversale — tous projets",
        "accent_color": "#D4AF37",
        "style": "corner_office",
        "agents": ["coo", "spec", "qa", "pm", "security_sentinel"],
    },
    "secretary_office": {
        "label": "Secrétariat de Direction",
        "description": "Filtrage, agenda, emails et coordination exécutive",
        "accent_color": "#D4AF37",
        "style": "executive_assistant",
        "agents": ["secretary"],
    },
    "app_office": {
        "label": "Pôle App",
        "description": "Développement applications mobiles",
        "accent_color": "#4FC3F7",
        "style": "modern_open",
        "agents": ["dev_app", "dev_backend", "rnd_product", "dev_frontend", "dev_integrator"],
    },
    "gaming_studio": {
        "label": "Studio Gaming",
        "description": "Conception et développement jeux vidéo",
        "accent_color": "#9C27B0",
        "style": "dark_atmospheric",
        "agents": [
            "game_director", "dev_gaming", "level_designer",
            "ai_programmer", "environment_artist", "technical_artist",
            "narrative_designer", "vfx_artist", "sound_designer", "qa_gaming",
        ],
    },
    "rnd_lab": {
        "label": "Pôle Innovation",
        "description": "Recherche, idéation et veille marché",
        "accent_color": "#26A69A",
        "style": "scientific",
        "agents": ["brainstorm", "rnd_agent", "rnd_dossier", "rnd_ceo", "rnd_committee"],
    },
    "comms_hub": {
        "label": "Hub Business",
        "description": "Marketing et contenu éditorial",
        "accent_color": "#FF7043",
        "style": "bright_creative",
        "agents": [
            "marketing", "content",
            "content_app", "content_gaming", "content_robo", "content_company",
            "brand", "ads",
            "rnd_social", "rnd_visual",
        ],
    },
    "hardware_workshop": {
        "label": "Atelier Robo",
        "description": "Hardware, embedded et robotique",
        "accent_color": "#78909C",
        "style": "industrial",
        "agents": [
            "hardware", "embedded_dev",
            "vision_ai", "electronics", "firmware", "mechanical",
            "industrial_design", "qa_robot", "safety", "simulation",
        ],
    },
    "accounting_office": {
        "label": "Comptabilité",
        "description": "Finances, budget et contrôle de gestion",
        "accent_color": "#FF7043",
        "style": "quiet_office",
        "agents": ["accounting", "controller"],
    },
    "analytics_room": {
        "label": "Reporting & Analytics",
        "description": "KPIs, métriques, business intelligence",
        "accent_color": "#378ADD",
        "style": "data_lab",
        "agents": ["analyst_business", "analyst_data"],
    },
}

TEAMS: dict[str, dict] = {
    "direction": {
        "label": "Direction",
        "color": "#D4AF37",
        "agents": ["spec", "qa", "pm"],  # coo + secretary exclus de la compétition
        "compete_metric": "validations_croisées",
    },
    "app": {
        "label": "Pôle App",
        "color": "#4FC3F7",
        "agents": ["dev_app", "dev_backend", "rnd_product", "dev_frontend", "dev_integrator"],
        "compete_metric": "features_livrées",
        "intra_competition": True,  # Théo vs Hao vs Inès vs Rayan
    },
    "gaming": {
        "label": "Studio Gaming",
        "color": "#9C27B0",
        "agents": [
            "game_director", "dev_gaming", "level_designer",
            "ai_programmer", "environment_artist", "technical_artist",
            "narrative_designer", "vfx_artist", "sound_designer", "qa_gaming",
        ],
        "compete_metric": "milestones_jeu",
        "intra_competition": True,
    },
    "innovation": {
        "label": "Pôle Innovation",
        "color": "#26A69A",
        "agents": ["brainstorm", "rnd_agent", "rnd_dossier", "rnd_ceo"],
        "compete_metric": "idées_validées_go",
        "intra_competition": True,  # Idris vs Alex vs Iris vs Noé
    },
    "business": {
        "label": "Hub Business",
        "color": "#FF7043",
        "agents": [
            "marketing", "content",
            "content_app", "content_gaming", "content_robo", "content_company",
            "brand", "ads",
            "rnd_social", "rnd_visual",
        ],
        "compete_metric": "impact_business",
    },
    "finance": {
        "label": "Finance",
        "color": "#FF7043",
        "agents": ["accounting", "controller"],
        "compete_metric": "précision_budgétaire",
        "intra_competition": True,  # Jules vs Rémi
    },
    "analytics": {
        "label": "Reporting & Analytics",
        "color": "#378ADD",
        "agents": ["analyst_business", "analyst_data"],
        "compete_metric": "insights_actionnés",
        "intra_competition": True,  # Layla vs Axel
    },
    "robo": {
        "label": "Atelier Robo",
        "color": "#78909C",
        "agents": [
            "hardware", "embedded_dev",
            "vision_ai", "electronics", "firmware", "mechanical",
            "industrial_design", "qa_robot", "safety", "simulation",
        ],
        "compete_metric": "composants_validés",
        "intra_competition": True,
    },
}
