"""R&D council agent — gauges, closure, and structured evaluation."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class RndCouncilCloseMixin:
    """Requires session/debate helpers and ``self.db``."""

    def compute_gauges(self, session_id: str) -> dict[str, Any]:
        rows = self.db.select("rnd_committee_votes", filters={"session_id": session_id}, order_by="round_index")
        latest: dict[str, dict[str, Any]] = {}
        for r in rows or []:
            latest[r["agent_id"]] = r

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
