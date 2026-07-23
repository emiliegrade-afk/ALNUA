"""Level Designer Agent — Finn Larsen, Level & Narrative Designer ALNUA Gaming."""

from __future__ import annotations

from agents.agent_base import AgentBase

from typing import Any

from agents.base import log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from database.supabase_client import SupabaseClient, get_supabase
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from skills.skill_langfuse import trace_agent


class LevelDesignerAgent(AgentBase):
    AGENT_NAME = "level_designer"

    SYSTEM_PROMPT = get_system_prompt("level_designer")


    @trace_agent("level_designer")
    def design_quest(
        self,
        quest_name: str,
        game: str,
        lore_context: str = "",
        player_level_range: str = "1-10",
        quest_type: str = "main",
    ) -> dict[str, Any]:
        """Conçoit une quête complète avec objectifs, dialogues et récompenses."""
        prompt = inject_learning_context(
            f"""Conçois une quête complète pour {game}.
Nom de la quête : {quest_name}
Type : {quest_type} (main|side|hidden|daily)
Niveau joueur cible : {player_level_range}
Contexte lore : {lore_context or 'Univers standard du jeu'}

Réponds en JSON :
{{
  "quest_id": "snake_case_id",
  "title": "{quest_name}",
  "type": "{quest_type}",
  "synopsis": "Résumé narratif (2-3 phrases)",
  "objectives": [
    {{ "id": 1, "description": "string", "type": "kill|collect|explore|talk|craft", "target": "string", "count": 1 }}
  ],
  "npc_dialogues": [
    {{ "npc": "string", "trigger": "start|progress|complete", "lines": ["string"] }}
  ],
  "rewards": {{
    "xp": 0,
    "gold": 0,
    "items": ["string"],
    "unlock": "string or null"
  }},
  "estimated_duration_minutes": 15,
  "narrative_notes": "Notes pour le Game Director"
}}""",
            self.AGENT_NAME, quest_name,
        )
        raw = self._complete(prompt, temperature=0.8, max_tokens=4096)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "design_quest",
            input_summary=f"{game} | {quest_name}",
            output_summary=f"Quête {quest_type} avec {len(result.get('objectives', []))} objectifs",
        )
        try:
            record_task_learning(self.AGENT_NAME, "design_quest", str(result)[:400], success=True)
        except Exception:
            pass
        return result

    @trace_agent("level_designer")
    def design_level(
        self,
        level_name: str,
        game: str,
        biome: str = "",
        difficulty: str = "medium",
        special_mechanics: str = "",
    ) -> dict[str, Any]:
        """Conçoit la structure et le flow d'un niveau."""
        prompt = inject_learning_context(
            f"""Conçois la structure d'un niveau pour {game}.
Nom : {level_name}
Biome / ambiance : {biome or 'À définir'}
Difficulté : {difficulty} (easy|medium|hard|boss)
Mécaniques spéciales : {special_mechanics or 'Aucune'}

Réponds en JSON :
{{
  "level_id": "snake_case",
  "title": "{level_name}",
  "biome": "{biome}",
  "flow": [
    {{ "zone": "Entrée", "type": "safe|combat|puzzle|exploration", "description": "string", "duration_seconds": 60 }}
  ],
  "key_encounters": [
    {{ "type": "enemy|boss|npc|event", "name": "string", "position": "string", "notes": "string" }}
  ],
  "collectibles": ["string"],
  "secrets": ["Description du secret caché"],
  "checkpoints": [1, 3, 5],
  "music_mood": "string",
  "design_notes": "Points d'attention pour Suki (Dev Gaming)"
}}""",
            self.AGENT_NAME, level_name,
        )
        raw = self._complete(prompt, temperature=0.75, max_tokens=4096)
        result = parse_json_response(raw)
        log_agent_action(
            self.db, self.AGENT_NAME, "design_level",
            input_summary=f"{game} | {level_name} | {difficulty}",
            output_summary=f"{len(result.get('flow', []))} zones, {len(result.get('key_encounters', []))} encounters",
        )
        return result

    @trace_agent("level_designer")
    def write_lore_entry(
        self,
        subject: str,
        game: str,
        lore_type: str = "history",
        length: str = "medium",
    ) -> dict[str, Any]:
        """Écrit une entrée de lore pour le codex du jeu."""
        length_guide = {"short": "100-150 mots", "medium": "250-350 mots", "long": "500-700 mots"}
        prompt = inject_learning_context(
            f"""Écris une entrée de lore pour le codex de {game}.
Sujet : {subject}
Type : {lore_type} (history|character|place|artifact|faction)
Longueur : {length_guide.get(length, '250-350 mots')}

Le ton doit être immersif, riche, cohérent avec un univers fantasy nordique.

Réponds en JSON :
{{
  "entry_id": "snake_case",
  "title": "string",
  "type": "{lore_type}",
  "content": "Texte complet de l'entrée lore",
  "tags": ["string"],
  "related_entries": ["autres entrées liées"]
}}""",
            self.AGENT_NAME, subject,
        )
        raw = self._complete(prompt, temperature=0.85, max_tokens=2048)
        return parse_json_response(raw)

    @trace_agent("level_designer")
    def balance_review(
        self,
        system: str,
        current_values: dict[str, Any],
        player_feedback: str = "",
    ) -> dict[str, Any]:
        """Analyse l'équilibrage d'un système de jeu et propose des ajustements."""
        prompt = inject_learning_context(
            f"""Analyse l'équilibrage de ce système de jeu.
Système : {system}
Valeurs actuelles : {current_values}
Feedback joueurs : {player_feedback or 'Aucun feedback disponible'}

Réponds en JSON :
{{
  "assessment": "Évaluation générale (1-2 phrases)",
  "issues": [{{ "parameter": "string", "current": "string", "problem": "string" }}],
  "recommendations": [{{ "parameter": "string", "change": "string", "rationale": "string" }}],
  "priority": "critical|high|medium|low"
}}""",
            self.AGENT_NAME, system,
        )
        raw = self._complete(prompt, temperature=0.4)
        return parse_json_response(raw)
