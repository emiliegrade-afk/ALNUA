"""Agent personas — façade BUG-004 (merge by bureau)."""
from __future__ import annotations

from config.personas_app import PERSONAS as _APP
from config.personas_comms import PERSONAS as _COMMS
from config.personas_direction import PERSONAS as _DIRECTION
from config.personas_gaming import PERSONAS as _GAMING
from config.personas_hardware import PERSONAS as _HARDWARE
from config.personas_ops import PERSONAS as _OPS
from config.personas_rnd import PERSONAS as _RND
from config.personas_rooms_teams import ROOMS, TEAMS

AGENT_PERSONAS: dict[str, dict] = {}
AGENT_PERSONAS.update(_DIRECTION)
AGENT_PERSONAS.update(_APP)
AGENT_PERSONAS.update(_GAMING)
AGENT_PERSONAS.update(_RND)
AGENT_PERSONAS.update(_COMMS)
AGENT_PERSONAS.update(_HARDWARE)
AGENT_PERSONAS.update(_OPS)

def get_persona(agent_id: str) -> dict | None:
    """Retourne le persona d'un agent ou None si inconnu."""
    from config.agent_models import normalize_agent_id
    return AGENT_PERSONAS.get(normalize_agent_id(agent_id))


def get_display_name(agent_id: str) -> str:
    """Prénom + Nom pour l'affichage UI."""
    p = get_persona(agent_id)
    if not p:
        return agent_id
    return f"{p['first_name']} {p['last_name']}"


def persona_first_name(agent_id: str) -> str:
    """Prénom canonique (events, copy courte)."""
    p = get_persona(agent_id)
    return p["first_name"] if p else agent_id


def persona_prompt_intro(agent_id: str, *, role: str | None = None) -> str:
    """Ligne d'identité canonique pour les system prompts LLM."""
    p = get_persona(agent_id)
    if not p:
        return f"Tu es l'agent {agent_id} d'ALNUA"
    role_part = role or p["role_label"].split("—")[0].strip()
    return f"Tu es {p['first_name']} {p['last_name']}, {role_part} d'ALNUA"


def get_room(agent_id: str) -> str | None:
    """Retourne la room ID de l'agent."""
    p = get_persona(agent_id)
    return p["room"] if p else None


def get_team(agent_id: str) -> str | None:
    """Retourne l'équipe de l'agent pour la compétition."""
    p = get_persona(agent_id)
    return p["team"] if p else None


def get_agents_in_room(room_id: str) -> list[str]:
    """Liste des agent_ids dans une pièce."""
    return ROOMS.get(room_id, {}).get("agents", [])


def get_competitive_context(agent_id: str, scores: dict | None = None) -> str:
    """
    Génère un bloc de contexte compétitif injecté dans le system prompt.
    Conçu pour activer la motivation intrinsèque de l'agent via :
    - Ancrage social (comparaison avec pairs)
    - Progrès vers paliers tangibles
    - Identité compétitive propre à chaque agent
    """
    from config.agent_models import normalize_agent_id
    agent_id = normalize_agent_id(agent_id)
    persona = AGENT_PERSONAS.get(agent_id)
    if not persona or not persona.get("competitive"):
        return ""

    team_id = persona["team"]
    team = TEAMS.get(team_id, {})
    name = persona["first_name"]
    scores = scores or {}

    my_score = scores.get(agent_id, 0)
    team_agents = [a for a in team.get("agents", []) if a != agent_id]
    team_scores = {a: scores.get(a, 0) for a in team_agents}

    lines = [f"[Contexte performance — {name}]"]

    # Score et position
    if my_score == 0:
        lines.append("Tu démarres ce mois à zéro. C'est le moment de marquer le territoire.")
    else:
        lines.append(f"Score ce mois : {my_score} pts.")

    # Dynamique compétitive
    if team_scores:
        best_peer_id = max(team_scores, key=team_scores.get)
        best_score = team_scores[best_peer_id]
        peer_persona = AGENT_PERSONAS.get(best_peer_id, {})
        peer_name = peer_persona.get("first_name", best_peer_id)

        if team.get("intra_competition"):
            # Compétition directe 1v1
            if my_score > best_score:
                gap = my_score - best_score
                lines.append(f"Tu devances {peer_name} de {gap} pts. Ne lâche pas — {peer_name} remonte toujours.")
            elif my_score == best_score:
                lines.append(f"À égalité avec {peer_name}. La prochaine tâche tranche.")
            else:
                gap = best_score - my_score
                lines.append(f"{peer_name} te devance de {gap} pts. Chaque tâche bien faite compte double.")
        else:
            # Compétition d'équipe
            team_total = sum(team_scores.values()) + my_score
            my_contribution_pct = int((my_score / team_total * 100)) if team_total > 0 else 0
            lines.append(f"Équipe {team.get('label', '')} : tu contribues {my_contribution_pct}% du score d'équipe.")

    # Paliers de bonus (récompenses réelles)
    if my_score >= 500:
        lines.append("🏆 Tier upgrade 30j actif. Tu joues avec le meilleur modèle disponible.")
    elif my_score >= 200:
        remaining = 500 - my_score
        lines.append(f"Tier upgrade 30j à {remaining} pts. Palier 500.")
    elif my_score >= 100:
        remaining = 200 - my_score
        lines.append(f"Tier upgrade 7j à {remaining} pts. Palier 200.")
    else:
        remaining = 100 - my_score
        lines.append(f"Pause café (réel) à {remaining} pts. Premier palier : 100.")

    lines.append("Sur cette tâche : sois précis, complet, impeccable.")
    lines.append(f"[/{name}]")

    return "\n".join(lines)
