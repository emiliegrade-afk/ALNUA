"""
rnd_council_agent.py — Conseil stratégique R&D (Phase 25, ROADMAP.md).

Débat multi-agents SANS dossier obligatoire (idéation pure ou évaluation
structurée) — contrairement à `RndCommitteeAgent` (agents/rnd_committee_agent.py)
qui exige toujours un `dossier_id` réel. Nouvelle orchestration légère, pas
une sous-classe : `RndCommitteeAgent` n'est ni touché ni étendu.

Les 5 membres du Conseil sont des personas dédiées au Conseil uniquement —
pas des agents/*.py individuels (ils n'ont pas de méthode solo, seulement une
participation aux délibérations), donc pas d'entrée dans
config/agent_personas.py : le frontend (AgentAvatar) rend un avatar à partir
du seul (agent_id, name) sans registre, et `agent_models.py::AGENT_TIERS.get`
retombe proprement sur le tier "standard" pour un agent_id inconnu.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from agents.base import LLMClient, parse_json_response
from database.supabase_client import get_supabase

logger = logging.getLogger(__name__)

SessionKind = Literal["strategic", "evaluation"]

COUNCIL_MEMBERS: dict[str, dict[str, str]] = {
    "council_chair": {
        "name": "Selene Marchetti",
        "role": "Présidente du Conseil",
        "focus": "synthèse, arbitrage, vision d'ensemble",
        "personality": (
            "Directe, structure le débat, tranche quand les avis divergent. "
            "Ne laisse jamais une discussion tourner en rond."
        ),
    },
    "council_innovation": {
        "name": "Kai Osei",
        "role": "Innovation & Vision",
        "focus": "originalité, différenciation, ambition produit",
        "personality": "Enthousiaste et créatif, pousse les idées audacieuses, challenge la timidité.",
    },
    "council_tech": {
        "name": "Freya Lindqvist",
        "role": "Faisabilité & Ingénierie",
        "focus": "faisabilité technique, complexité, délais réalistes",
        "personality": "Rigoureuse et terre-à-terre, pointe les risques techniques sans jamais dramatiser.",
    },
    "council_business": {
        "name": "Darius Whitmore",
        "role": "Business & Marché",
        "focus": "marché, ROI, positionnement concurrentiel",
        "personality": "Pragmatique, pense en termes de coût d'opportunité et de traction réelle.",
    },
    "council_data": {
        "name": "Amara Solis",
        "role": "Données & Risques",
        "focus": "signaux chiffrés, hypothèses à vérifier, risques quantifiables",
        "personality": "Sceptique constructive, demande toujours « sur quelles données on se base ? ».",
    },
}

COUNCIL_RULES = """
RÈGLES DU CONSEIL STRATÉGIQUE ALNUA :
- Français, ton direct de comité de direction — pas de bullshit marketing.
- Maximum 80 mots pour ta remarque (content) — une position claire, pas un essai.
- Conclus TOUJOURS par un verdict individuel (GO/MAYBE/NO), une confiance (0-100),
  et 4 scores 0-100 : feasibility (faisabilité technique), innovation (originalité),
  roi (retour sur investissement estimé), risk (niveau de risque, 100 = très risqué).
- stance_text = une phrase courte (moins de 15 mots) résumant ta position, façon
  bulle de dialogue.
- N'écris jamais le nom d'un collègue dans stance_text.
- Ne répète pas ce qu'un collègue vient de dire — apporte un angle différent ou objecte.
"""


def _system_prompt(member_id: str) -> str:
    m = COUNCIL_MEMBERS[member_id]
    return (
        f"Tu es {m['name']}, {m['role']} au Conseil stratégique ALNUA.\n"
        f"Angle : {m['focus']}.\n"
        f"Personnalité : {m['personality']}\n"
        f"{COUNCIL_RULES}\n\n"
        "Réponds UNIQUEMENT en JSON, sans fences markdown :\n"
        '{"content": "ta remarque, <=80 mots", "stance_text": "position courte", '
        '"verdict": "GO|MAYBE|NO", "confidence_pct": 0, '
        '"axis_scores": {"feasibility": 0, "innovation": 0, "roi": 0, "risk": 0}}'
    )


class RndCouncilAgent:
    def __init__(self) -> None:
        self.db = get_supabase()
        self.llm = LLMClient()

    # ------------------------------------------------------------------ #
    # Sessions
    # ------------------------------------------------------------------ #

    def start_session(
        self,
        *,
        kind: SessionKind,
        topic: str = "",
        idea_id: str | None = None,
        structured_input: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        session_id = f"council_{uuid.uuid4().hex[:12]}"
        title = topic.strip() or ("Évaluation structurée" if kind == "evaluation" else "Conseil stratégique")
        row = {
            "session_id": session_id,
            "dossier_id": None,
            "session_kind": kind,
            "idea_id": idea_id,
            "structured_input": structured_input,
            "topic": title,
            "title": title,
            "mode": "free",
            "team": [{"agent_id": k, "name": v["name"], "role": v["role"]} for k, v in COUNCIL_MEMBERS.items()],
            "status": "active",
        }
        session = self.db.insert("rnd_committee_sessions", row)
        logger.info("[RndCouncil] session %s créée (kind=%s)", session_id, kind)
        return session

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        rows = self.db.select("rnd_committee_sessions", filters={"session_id": session_id}, limit=1)
        return rows[0] if rows else None

    def list_messages(self, session_id: str, *, limit: int = 200) -> list[dict[str, Any]]:
        return list(
            self.db.select(
                "rnd_committee_messages",
                filters={"session_id": session_id},
                order_by="created_at",
                limit=limit,
            )
            or []
        )

    def _next_round_index(self, session_id: str) -> int:
        rows = self.db.select(
            "rnd_committee_votes",
            filters={"session_id": session_id},
            order_by="round_index",
            ascending=False,
            limit=1,
        )
        if not rows:
            return 0
        return int(rows[0]["round_index"]) + 1

    # ------------------------------------------------------------------ #
    # Débat
    # ------------------------------------------------------------------ #

    async def post_message(self, session_id: str, message: str, *, actor: str = "emilie") -> dict[str, Any]:
        session = self.get_session(session_id)
        if not session or session.get("status") != "active":
            raise ValueError("Session Conseil introuvable ou fermée")

        text = message.strip()
        if not text:
            raise ValueError("Message vide")

        user_msg = self.db.insert(
            "rnd_committee_messages",
            {"session_id": session_id, "dossier_id": None, "speaker": actor, "role": "user", "content": text},
        )

        history = self.list_messages(session_id)
        transcript = "\n".join(f"{h['speaker']}: {h['content']}" for h in history[-20:])
        round_index = self._next_round_index(session_id)

        async def _ask(member_id: str) -> dict[str, Any]:
            raw = await self.llm.complete_async(
                system=_system_prompt(member_id),
                user=f"Historique de la discussion :\n{transcript}\n\nDonne ta position.",
                agent_id=member_id,
                method_name="council_post_message",
                temperature=0.6,
            )
            try:
                parsed = parse_json_response(raw)
            except Exception:
                parsed = {
                    "content": raw[:400],
                    "stance_text": raw[:80],
                    "verdict": "MAYBE",
                    "confidence_pct": 50,
                    "axis_scores": {},
                }
            return {"member_id": member_id, **parsed}

        results = await asyncio.gather(*(_ask(mid) for mid in COUNCIL_MEMBERS), return_exceptions=True)

        new_messages: list[dict[str, Any]] = [user_msg]
        new_votes: list[dict[str, Any]] = []
        for member_id, res in zip(COUNCIL_MEMBERS.keys(), results):
            m = COUNCIL_MEMBERS[member_id]
            if isinstance(res, Exception):
                logger.warning("[RndCouncil] membre %s a échoué : %s", member_id, res)
                continue

            msg_row = self.db.insert(
                "rnd_committee_messages",
                {
                    "session_id": session_id,
                    "dossier_id": None,
                    "speaker": member_id,
                    "role": "assistant",
                    "content": str(res.get("content") or ""),
                    "metadata": {"name": m["name"], "role_label": m["role"]},
                },
            )
            new_messages.append(msg_row)

            axis = res.get("axis_scores") or {}
            verdict = res.get("verdict") if res.get("verdict") in ("GO", "MAYBE", "NO") else "MAYBE"
            try:
                confidence = max(0, min(100, int(res.get("confidence_pct") or 50)))
            except (TypeError, ValueError):
                confidence = 50

            vote_row = self.db.insert(
                "rnd_committee_votes",
                {
                    "session_id": session_id,
                    "agent_id": member_id,
                    "agent_name": m["name"],
                    "verdict": verdict,
                    "confidence_pct": confidence,
                    "axis_scores": {
                        "feasibility": axis.get("feasibility"),
                        "innovation": axis.get("innovation"),
                        "roi": axis.get("roi"),
                        "risk": axis.get("risk"),
                    },
                    "stance_text": str(res.get("stance_text") or "").strip()[:200] or m["role"],
                    "round_index": round_index,
                    "is_final": False,
                },
            )
            new_votes.append(vote_row)

        return {"session_id": session_id, "messages": new_messages, "votes": new_votes}

    # ------------------------------------------------------------------ #
    # Jauges & clôture
    # ------------------------------------------------------------------ #

    def compute_gauges(self, session_id: str) -> dict[str, Any]:
        rows = self.db.select("rnd_committee_votes", filters={"session_id": session_id}, order_by="round_index")
        latest: dict[str, dict[str, Any]] = {}
        for r in rows or []:
            latest[r["agent_id"]] = r  # round_index ascendant → la dernière écrase les précédentes

        per_agent = list(latest.values())
        if not per_agent:
            return {
                "consensus_pct": 0,
                "feasibility_pct": 0,
                "innovation_pct": 0,
                "roi_pct": 0,
                "risk_pct": 0,
                "per_agent": [],
            }

        verdict_counts: dict[str, int] = {}
        for v in per_agent:
            verdict_counts[v["verdict"]] = verdict_counts.get(v["verdict"], 0) + 1
        majority = max(verdict_counts.values())
        consensus_pct = round(100 * majority / len(per_agent))

        def _avg(key: str) -> int:
            vals = [
                (v.get("axis_scores") or {}).get(key)
                for v in per_agent
                if (v.get("axis_scores") or {}).get(key) is not None
            ]
            return round(sum(vals) / len(vals)) if vals else 0

        return {
            "consensus_pct": consensus_pct,
            "feasibility_pct": _avg("feasibility"),
            "innovation_pct": _avg("innovation"),
            "roi_pct": _avg("roi"),
            "risk_pct": _avg("risk"),
            "per_agent": [
                {
                    "agent_id": v["agent_id"],
                    "name": v["agent_name"],
                    "verdict": v["verdict"],
                    "confidence_pct": v["confidence_pct"],
                    "stance_text": v["stance_text"],
                }
                for v in per_agent
            ],
        }

    def close_session(self, session_id: str) -> dict[str, Any]:
        session = self.get_session(session_id)
        if not session:
            raise ValueError("Session introuvable")

        rows = self.db.select("rnd_committee_votes", filters={"session_id": session_id}, order_by="round_index")
        latest: dict[str, dict[str, Any]] = {}
        for r in rows or []:
            latest[r["agent_id"]] = r
        for row in latest.values():
            self.db.update("rnd_committee_votes", row["id"], {"is_final": True})

        gauges = self.compute_gauges(session_id)
        self.db.update(
            "rnd_committee_sessions",
            session["id"],
            {"status": "closed", "closed_at": datetime.now(timezone.utc).isoformat()},
        )

        verdict_counts: dict[str, int] = {}
        for v in gauges["per_agent"]:
            verdict_counts[v["verdict"]] = verdict_counts.get(v["verdict"], 0) + 1
        recommendation = max(verdict_counts, key=lambda k: verdict_counts[k]) if verdict_counts else None

        # `deliberated=False` distingue "le conseil a vraiment tranché MAYBE"
        # d'un conseil qui n'a jamais pu délibérer (ex. LLM indisponible) —
        # sans ça, une session à 0 vote afficherait une fausse "Décision
        # Collective : MAYBE, 0% consensus" comme si c'était un vrai verdict.
        return {
            "session_id": session_id,
            "gauges": gauges,
            "recommendation": recommendation or "MAYBE",
            "consensus_pct": gauges["consensus_pct"],
            "deliberated": bool(verdict_counts),
        }

    async def evaluate(
        self,
        *,
        topic: str,
        structured_input: dict[str, Any],
        idea_id: str | None = None,
    ) -> dict[str, Any]:
        """Conseil IA (input structuré → débat → Décision Collective) — un
        seul appel enchaîne start → débat → clôture, pour le formulaire
        "budget/équipe/délai" qui n'attend pas une conversation continue."""
        session = self.start_session(
            kind="evaluation", topic=topic, idea_id=idea_id, structured_input=structured_input
        )
        question = (
            f"Nouveau projet à évaluer : {topic}\n"
            f"Budget : {structured_input.get('budget_eur', '—')} €\n"
            f"Taille d'équipe : {structured_input.get('team_size', '—')}\n"
            f"Délai visé : {structured_input.get('timeframe_weeks', '—')} semaines\n"
            f"Type de produit : {structured_input.get('product_type', '—')}\n\n"
            "Faut-il lancer ce projet ?"
        )
        debate = await self.post_message(session["session_id"], question, actor="emilie")
        closed = self.close_session(session["session_id"])
        if not closed["deliberated"]:
            raise RuntimeError(
                "Le Conseil n'a pas pu délibérer — tous les membres ont échoué "
                "(LLM indisponible ou crédits OpenRouter épuisés). Aucune décision fabriquée."
            )
        return {"session_id": session["session_id"], "debate": debate, **closed}
