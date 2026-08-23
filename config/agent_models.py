je"""

config/agent_models.py — Sélection de modèle LLM par agent.



Priorité de résolution (du plus spécifique au plus général) :

  1. Variable d'env  AGENT_MODEL_{AGENT_ID}   (ex: AGENT_MODEL_COO=openrouter/anthropic/claude-opus-4)

  2. Fichier de config  data/agent_models.json  (choix dans Paramètres /settings)

  3. Tier automatique basé sur le rôle de l'agent (premium / standard / fast)



Mode AUTO : modèle selon le tier de l'agent. Les choix dans Paramètres priment sur tout.



Façade : siblings under ``config/agent_models_*.py`` keep each module ≤ ~300 lines.

"""

from __future__ import annotations



from config.agent_models_catalog import (  # noqa: F401 — re-export

    AVAILABLE_MODELS,

    MODEL_CATEGORIES,

    MODEL_CATEGORY_ORDER,

    get_enriched_available_models,

)

from config.agent_models_registry import (  # noqa: F401 — re-export

    AGENT_ID_ALIASES,

    AGENT_TIERS,

    CODING_AGENT_IDS,

    MEMORY_DISPLAY_ALIASES,

    TIER_DEFAULTS,

    TIER_MODELS,

    memory_agent_id,

    normalize_agent_id,

)

from config.agent_models_resolve import (  # noqa: F401 — re-export

    _CONFIG_FILE,

    get_all_agent_models,

    get_coding_model_aider,

    get_coding_model_for_agent,

    get_coding_model_openrouter,

    get_model_for_agent,

    set_agent_model,

)



__all__ = [

    "AGENT_ID_ALIASES",

    "AGENT_TIERS",

    "AVAILABLE_MODELS",

    "CODING_AGENT_IDS",

    "MEMORY_DISPLAY_ALIASES",

    "MODEL_CATEGORIES",

    "MODEL_CATEGORY_ORDER",

    "TIER_DEFAULTS",

    "TIER_MODELS",

    "_CONFIG_FILE",

    "get_all_agent_models",

    "get_coding_model_aider",

    "get_coding_model_for_agent",

    "get_coding_model_openrouter",

    "get_enriched_available_models",

    "get_model_for_agent",

    "memory_agent_id",

    "normalize_agent_id",

    "set_agent_model",

]


