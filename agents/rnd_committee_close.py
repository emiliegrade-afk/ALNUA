"""R&D committee agent — close session, reports, session queries."""
from __future__ import annotations

import logging
from typing import Any

from agents.base import log_agent_action
from skills.skill_langfuse import trace_agent

logger = logging.getLogger(__name__)


class RndCommitteeCloseMixin:
    """Requires ``self.repo``, ``self.committee``, section helpers from ``RndCommitteeLlmMixin``."""

    @trace_agent("rnd_committee")
    def close_session(
        self,
        dossier_id: str,
        session_id: str,
        *,
        apply_sections: bool = True,
        generate_ceo_package: bool = False,
        actor: str = "emilie",
    ) -> dict[str, Any]:
        session = self.committee.get_session(session_id)
        if not session:
            raise ValueError("Session introuvable")

        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")

        history = self.committee.list_messages(session_id)
        synthesis_md = ""
        committee_report_md = ""
        updated_sections: list[str] = []

        from agents.rnd_ceo_agent import RndCeoAgent

        ceo_agent = RndCeoAgent()

        if history:
            committee_report_md = ceo_agent.generate_committee_report(
                dossier_id, history, dossier=dossier
            )
            self.repo.update_dossier(
                dossier_id, {"committee_report_md": committee_report_md}
            )
            synthesis_md = committee_report_md

            self.committee.add_message(
                session_id=session_id,
                dossier_id=dossier_id,
                speaker="pm",
                role="assistant",
                content=committee_report_md,
                metadata={"synthesis": True, "committee_report": True},
            )

            if apply_sections:
                updated_sections = self._apply_synthesis_to_sections(
                    dossier_id, dossier, committee_report_md
                )

        closed = self.committee.close_session(session_id)
        had_user_messages = any(m.get("role") == "user" for m in history)

        refreshed = self.repo.get_dossier(dossier_id) or dossier
        validated_count = refreshed.sections_validated_count
        total = refreshed.sections_total_count
        if validated_count >= total * 0.6:
            new_status = "ready_for_ceo"
        elif validated_count > 0:
            new_status = "partial_validated"
        elif committee_report_md or had_user_messages:
            new_status = "partial_validated"
        else:
            new_status = "draft"
        self.repo.update_dossier(dossier_id, {"status": new_status})

        self.repo.log_event(
            dossier_id,
            "committee_closed",
            actor,
            {
                "session_id": session_id,
                "sections_updated": updated_sections,
                "new_status": new_status,
                "has_committee_report": bool(committee_report_md),
            },
        )

        ceo_package_result: dict[str, Any] | None = None
        ceo_package_error: str | None = None
        if generate_ceo_package and new_status in ("ready_for_ceo", "partial_validated"):
            try:
                ceo_package_result = ceo_agent.generate_package(dossier_id, actor=actor)
            except Exception as exc:
                ceo_package_error = str(exc)
                logger.warning("auto ceo package on close failed: %s", exc)

        log_agent_action(
            self.db, self.AGENT_NAME, "close_session",
            input_summary=f"dossier_id={dossier_id} session={session_id}",
            output_summary=f"status={new_status} sections_updated={len(updated_sections)}",
        )
        return {
            "session": closed,
            "synthesis_md": synthesis_md,
            "committee_report_md": committee_report_md,
            "sections_updated": updated_sections,
            "dossier_status": new_status,
            "ceo_package": ceo_package_result,
            "ceo_package_error": ceo_package_error,
        }

    def get_session_with_messages(
        self, dossier_id: str, session_id: str
    ) -> dict[str, Any]:
        session = self.committee.get_session(session_id)
        if not session or str(session.get("dossier_id")) != str(dossier_id):
            raise ValueError("Session introuvable")
        return {
            "session": session,
            "messages": self.committee.list_messages(session_id),
        }

    def list_sessions(self, dossier_id: str) -> list[dict[str, Any]]:
        return self.committee.list_sessions(dossier_id)

    @trace_agent("rnd_committee")
    def generate_session_report(
        self,
        dossier_id: str,
        session_id: str,
        *,
        actor: str = "emilie",
    ) -> dict[str, Any]:
        """Generate structured CR without closing the committee session."""
        session = self.committee.get_session(session_id)
        if not session:
            raise ValueError("Session introuvable")
        if str(session.get("dossier_id")) != str(dossier_id):
            raise ValueError("Session ne correspond pas au dossier")

        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")

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
            metadata={"committee_report": True, "on_demand": True},
        )

        self.repo.log_event(
            dossier_id,
            "committee_report_generated",
            actor,
            {"session_id": session_id, "on_demand": True},
        )
        log_agent_action(
            self.db, self.AGENT_NAME, "generate_session_report",
            input_summary=f"dossier_id={dossier_id} session={session_id}",
            output_summary="rapport de session généré",
        )
        return {"committee_report_md": report_md, "message": msg}
