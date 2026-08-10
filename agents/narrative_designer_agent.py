"""Narrative Designer Agent — Sable Winters, écriture narrative ALNUA Gaming."""
from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from config.agent_operating_spec import get_system_prompt
from skills.skill_langfuse import trace_agent


class NarrativeDesignerAgent(AgentBase):
    AGENT_NAME = "narrative_designer"
    SYSTEM_PROMPT = get_system_prompt("narrative_designer")

    @trace_agent("narrative_designer")
    def write_dialogue(
        self,
        npc_name: str,
        game: str,
        context: str = "",
        tone: str = "neutre",
    ) -> dict[str, Any]:
        """Écrit les lignes de dialogue d'un PNJ secondaire, cohérentes avec le canon."""
        prompt = f"""Écris les dialogues d'un PNJ secondaire pour {game}.
PNJ : {npc_name}
Contexte : {context or 'PNJ de quête annexe ou marchand'}
Ton : {tone}

Réponds en JSON :
{{
  "npc": "{npc_name}",
  "voice_notes": "2-3 traits de personnalité qui guident le ton",
  "lines": [
    {{ "trigger": "greeting|quest_offer|quest_progress|quest_complete|idle", "text": "string" }}
  ],
  "codex_entry": "Court texte codex complémentaire (optionnel, string vide si non pertinent)",
  "canon_check": "Points à valider avec Mira Chen avant intégration"
}}"""
        return self.run_json_task(
            action="write_dialogue",
            prompt=prompt,
            learning_key=npc_name,
            input_summary=f"{game} | {npc_name} | {tone}",
            output_summary=lambda r: f"{len(r.get('lines', []))} lignes de dialogue",
            temperature=0.8,
            max_tokens=2048,
        )

    @trace_agent("narrative_designer")
    def search_canon(self, query: str, game: str = "Wyrdheim") -> dict[str, Any]:
        """Phase 21 — search lore/GDD canon before writing (real skill)."""
        from skills.skill_lore_database import search_lore

        hits = search_lore(query, project=game, limit=8)
        return {
            "ok": True,
            "query": query,
            "game": game,
            "hits": hits,
            "count": len(hits),
        }

    @trace_agent("narrative_designer")
    def probe_ue58(self) -> dict[str, Any]:
        from skills.skill_ue58 import probe_for_agent

        return probe_for_agent(self.AGENT_NAME)
