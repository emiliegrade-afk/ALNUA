"""R&D committee agent — session start and messaging."""
from __future__ import annotations

from typing import Any

from agents.base import log_agent_action
from agents.rnd_committee_constants import REPORT_INTENT_RE
from services.rnd_committee import build_committee_team
from skills.skill_langfuse import trace_agent


class RndCommitteeSessionMixin:
    """Requires ``self.repo``, ``self.committee``, LLM helpers from ``RndCommitteeLlmMixin``."""

    @trace_agent("rnd_committee")
    def start_session(
        self,
        dossier_id: str,
        *,
        mode: str = "free",
        active_section: str | None = None,
        force_new: bool = False,
        actor: str = "emilie",
    ) -> dict[str, Any]:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")

        existing = self.committee.get_active_session(dossier_id)
        if existing and not force_new:
            messages = self.committee.list_messages(existing["session_id"])
            return {
                "session": existing,
                "messages": messages,
                "resumed": True,
                "read_only": False,
            }

        if not force_new:
            closed = self.committee.get_latest_closed_session(dossier_id)
            if closed:
                messages = self.committee.list_messages(closed["session_id"])
                if messages:
                    return {
                        "session": closed,
                        "messages": messages,
                        "resumed": True,
                        "read_only": True,
                    }

        team = build_committee_team(dossier.domain)
        session = self.committee.create_session(
            dossier_id,
            title=f"Comité — {dossier.title}",
            team=team,
            mode=mode,
            active_section=active_section,
        )

        self.repo.update_dossier(
            dossier_id,
            {"status": "committee_active", "committee_team": team},
        )
        idea_row = self.repo.get_idea_db_row(dossier.idea_id) or {}
        if idea_row.get("id"):
            self.repo.db.update(
                "rnd_ideas",
                idea_row["id"],
                {"lifecycle_status": "in_committee"},
            )

        context = self._dossier_context(dossier)
        self.committee.add_message(
            session_id=session["session_id"],
            dossier_id=dossier_id,
            speaker="system",
            role="system",
            content=(
                f"Comité R&D ouvert sur **{dossier.title}**. "
                f"Équipe : {', '.join(m['name'] for m in team)}. "
                "Pose tes questions, challenge une section, ou demande une synthèse."
            ),
        )

        messages = [self.committee.list_messages(session["session_id"])[-1]]
        if self._should_use_llm():
            openings = self._generate_kickoff(team, context)
            for item in openings:
                mid = item.get("speaker", "pm")
                content = str(item.get("content", "")).strip()
                if not content:
                    continue
                msg = self.committee.add_message(
                    session_id=session["session_id"],
                    dossier_id=dossier_id,
                    speaker=mid,
                    role="assistant",
                    content=content,
                    metadata={"kickoff": True},
                )
                messages.append(msg)

        self.repo.log_event(
            dossier_id,
            "committee_started",
            actor,
            {"session_id": session["session_id"], "team_size": len(team)},
        )
        log_agent_action(
            self.db, self.AGENT_NAME, "start_session",
            input_summary=f"dossier_id={dossier_id} mode={mode}",
            output_summary=f"session={session['session_id']} team_size={len(team)}",
        )
        return {
            "session": session,
            "messages": messages,
            "resumed": False,
            "read_only": False,
        }

    @trace_agent("rnd_committee")
    def post_message(
        self,
        dossier_id: str,
        session_id: str,
        message: str,
        *,
        target_speaker: str | None = None,
        actor: str = "emilie",
    ) -> dict[str, Any]:
        session = self.committee.get_session(session_id)
        if not session or session.get("status") != "active":
            raise ValueError("Session comité introuvable ou fermée")
        if str(session.get("dossier_id")) != str(dossier_id):
            raise ValueError("Session ne correspond pas au dossier")

        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")

        text = message.strip()
        if not text:
            raise ValueError("Message vide")

        user_msg = self.committee.add_message(
            session_id=session_id,
            dossier_id=dossier_id,
            speaker=actor,
            role="user",
            content=text,
            section_key=session.get("active_section"),
        )

        responses: list[dict[str, Any]] = []

        if REPORT_INTENT_RE.search(text):
            history = self.committee.list_messages(session_id)
            from agents.rnd_ceo_agent import RndCeoAgent

            report_md = RndCeoAgent().generate_committee_report(
                dossier_id, history, dossier=dossier
            )
            self.repo.update_dossier(dossier_id, {"committee_report_md": report_md})
            msg = self.committee.add_message(
                session_id=session_id,
                dossier_id=dossier_id,
                speaker="pm",
                role="assistant",
                content=report_md,
                metadata={"committee_report": True},
            )
            responses.append(msg)
            self.repo.log_event(
                dossier_id,
                "committee_report_generated",
                actor,
                {"session_id": session_id, "intent": "nl"},
            )
            log_agent_action(
                self.db, self.AGENT_NAME, "post_message",
                input_summary=f"dossier_id={dossier_id} session={session_id} intent=report",
                output_summary="rapport de comité généré",
            )
            return {"user_message": user_msg, "responses": responses}

        if self._should_use_llm():
            team_ids = [m["id"] for m in session.get("team") or []]
            responders = self._pick_responders(
                text,
                team_ids,
                target_speaker=target_speaker,
                active_section=session.get("active_section"),
            )
            history = self.committee.list_messages(session_id)
            context = self._dossier_context(dossier)
            for member_id in responders[:3]:
                reply = self._member_reply(
                    member_id,
                    context,
                    history,
                    text,
                )
                if reply:
                    msg = self.committee.add_message(
                        session_id=session_id,
                        dossier_id=dossier_id,
                        speaker=member_id,
                        role="assistant",
                        content=reply,
                        section_key=session.get("active_section"),
                    )
                    responses.append(msg)

        self.repo.log_event(
            dossier_id,
            "committee_message",
            actor,
            {"session_id": session_id, "responses": len(responses)},
        )
        log_agent_action(
            self.db, self.AGENT_NAME, "post_message",
            input_summary=f"dossier_id={dossier_id} session={session_id}",
            output_summary=f"{len(responses)} réponse(s)",
        )
        return {"user_message": user_msg, "responses": responses}
