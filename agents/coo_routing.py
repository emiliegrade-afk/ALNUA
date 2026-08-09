"""COO specialized-agent routing — extracted from coo_agent (Vague 2 / BUG-004)."""

from __future__ import annotations

# Ordre important : expressions longues avant sous-chaînes (ex. "raspberry pi" avant "bom")
AGENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "embedded": (
        "raspberry pi", "python pi", "firmware", "ssh eve", "naia-embodied",
        "déployer pi", "deployer pi",
    ),
    "game_director": (
        "wyrdheim", "lore", "quête", "quete", "game design", "level design",
        "économie jeu", "economie jeu", "naïa world", "naia world",
    ),
    "dev_gaming": (
        "blueprint", "c++", "ue5", "unreal", "modding", "websocket ue5",
        "looking glass", "nwiro",
    ),
    "hardware": (
        "composant", "bom", "eve hardware", "circuit", "capteur", "moteur", "servo",
    ),
    "marketing": (
        "seo", "discord", "communauté", "communaute", "réseaux sociaux",
        "reseaux sociaux", "contenu", "tweet", "patch notes", "changelog",
    ),
}


def route_to_agent(
    instruction: str,
    telegram_notify_fn=None,
) -> tuple[str, str | None]:
    """
    Route une instruction vers le bon agent spécialisé.
    Retourne (agent_name, response). response=None si fallback COO.
    """
    instruction_lower = instruction.lower()

    for agent_name, keywords in AGENT_KEYWORDS.items():
        if not any(kw in instruction_lower for kw in keywords):
            continue

        if agent_name == "game_director":
            from agents.game_director_agent import GameDirectorAgent

            return agent_name, GameDirectorAgent(telegram_notify_fn).handle_instruction(
                instruction
            )
        if agent_name == "dev_gaming":
            from agents.dev_gaming_agent import DevGamingAgent

            return agent_name, DevGamingAgent(telegram_notify_fn).handle_instruction(
                instruction
            )
        if agent_name == "hardware":
            from agents.hardware_agent import HardwareAgent

            return agent_name, HardwareAgent(telegram_notify_fn).handle_instruction(
                instruction
            )
        if agent_name == "embedded":
            from agents.embedded_dev_agent import EmbeddedDevAgent

            return agent_name, EmbeddedDevAgent(telegram_notify_fn).handle_instruction(
                instruction
            )
        if agent_name == "marketing":
            from agents.marketing_agent import MarketingAgent

            return agent_name, MarketingAgent(telegram_notify_fn).handle_instruction(
                instruction
            )

    return "coo", None
