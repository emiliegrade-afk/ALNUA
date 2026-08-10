"""R&D council agent — multi-member debate."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from agents.base import parse_json_response
from agents.rnd_council_constants import COUNCIL_MEMBERS, council_system_prompt

logger = logging.getLogger(__name__)


class RndCouncilDebateMixin:
    """Requires session helpers and ``self.llm``."""

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
                system=council_system_prompt(member_id),
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
