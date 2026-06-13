"""
rnd_committee_agent.py — Multi-agent R&D committee in natural language (phase 3).
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any

from agents.base import LLMClient, parse_json_response
from agents.rnd_committee_prompts import (
    KICKOFF_USER,
    build_member_system,
)
from services.rnd_committee import (
    COMMITTEE_MEMBERS,
    build_committee_team,
    get_committee_repository,
    member_label,
)
from services.rnd_repository import get_rnd_repository
from services.rnd_schemas import RndDossierOut

logger = logging.getLogger(__name__)

MENTION_RE = re.compile(r"@(\w+)", re.IGNORECASE)
REPORT_INTENT_RE = re.compile(
    r"fais.?moi le dossier|génère.?le cr|genere.?le cr|compte.?rendu|"
    r"synthèse de clôture|synthese de cloture|handoff ceo|dossier ceo",
    re.IGNORECASE,
)

KEYWORD_ROUTING: list[tuple[re.Pattern[str], list[str]]] = [
    (re.compile(r"financ|prix|tarif|revenu|roi|capex|business", re.I), ["accounting", "pm"]),
    (re.compile(r"techni|stack|mvp|code|api|supabase|faisabilit", re.I), ["spec", "dev_app"]),
    (re.compile(r"marché|concurrent|positionn|acquisition|go-to-market", re.I), ["marketing", "pm"]),
    (re.compile(r"social|teaser|communaut|contenu|lancement", re.I), ["content", "marketing"]),
    (re.compile(r"jeu|gameplay|joueur|lore", re.I), ["game_director", "dev_gaming"]),
    (re.compile(r"hardware|firmware|capteur|bom|fabrication", re.I), ["hardware", "embedded_dev"]),
]


class RndCommitteeAgent:
    AGENT_NAME = "rnd_committee_agent"

    def __init__(self) -> None:
        self.repo = get_rnd_repository()
        self.committee = get_committee_repository()
        self.llm = LLMClient()

    def start_session(
        self,
        dossier_id: str,
        *,
        mode: str = "free",
        active_section: str | None = None,
        actor: str = "emilie",
    ) -> dict[str, Any]:
        dossier = self.repo.get_dossier(dossier_id)
        if not dossier:
            raise ValueError("Dossier introuvable")

        existing = self.committee.get_active_session(dossier_id)
        if existing:
            messages = self.committee.list_messages(existing["session_id"])
            return {
                "session": existing,
                "messages": messages,
                "resumed": True,
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
        return {"session": session, "messages": messages, "resumed": False}

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
        return {"user_message": user_msg, "responses": responses}

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
        validated_count = dossier.sections_validated_count
        total = dossier.sections_total_count
        new_status = (
            "ready_for_ceo"
            if validated_count >= total * 0.6
            else "partial_validated"
            if validated_count > 0
            else "draft"
        )
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
        if generate_ceo_package and new_status in ("ready_for_ceo", "partial_validated"):
            try:
                ceo_package_result = ceo_agent.generate_package(dossier_id, actor=actor)
            except Exception as exc:
                logger.warning("auto ceo package on close failed: %s", exc)

        return {
            "session": closed,
            "synthesis_md": synthesis_md,
            "committee_report_md": committee_report_md,
            "sections_updated": updated_sections,
            "dossier_status": new_status,
            "ceo_package": ceo_package_result,
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
        return {"committee_report_md": report_md, "message": msg}

    @staticmethod
    def _should_use_llm() -> bool:
        if os.getenv("RND_DOSSIER_USE_LLM", "true").lower() in ("0", "false", "no"):
            return False
        return bool(LLMClient()._settings.openrouter_api_key.strip())

    def _dossier_context(self, dossier: RndDossierOut) -> str:
        parts = [
            f"Titre : {dossier.title}",
            f"Domaine : {dossier.domain}",
            f"Statut : {dossier.status}",
        ]
        if dossier.finance_json:
            fj = dossier.finance_json
            rev = fj.get("revenue_hypothesis") or {}
            parts.append(
                f"Finance : CAPEX {fj.get('capex_eur')} EUR, "
                f"M12 {rev.get('m12_monthly_run_rate_eur')} EUR/mois, "
                f"verdict {fj.get('verdict_finance')}"
            )
        for sec in dossier.sections:
            if sec.section_key in (
                "problem", "solution", "market", "mvp", "business_case", "risks", "decision",
            ):
                parts.append(f"\n## {sec.title}\n{sec.content_md[:1200]}")
        return "\n".join(parts)

    def _generate_kickoff(
        self, team: list[dict[str, Any]], context: str
    ) -> list[dict[str, str]]:
        member_ids = ", ".join(m["id"] for m in team)
        try:
            raw = self.llm.complete(
                build_member_system("pm", context),
                KICKOFF_USER.format(members=member_ids),
                agent_id="pm",
                temperature=0.5,
                max_tokens=2000,
            )
            data = parse_json_response(raw)
            openings = data.get("openings") or []
            return [
                {"speaker": str(o.get("speaker", "pm")), "content": str(o.get("content", ""))}
                for o in openings
                if o.get("content")
            ]
        except Exception as exc:
            logger.warning("committee kickoff failed: %s", exc)
            return [
                {
                    "speaker": "pm",
                    "content": (
                        "Dossier prêt pour review. Je propose qu'on valide d'abord le scope MVP "
                        "et les hypothèses pricing avant d'aller au CEO."
                    ),
                }
            ]

    def _pick_responders(
        self,
        message: str,
        team_ids: list[str],
        *,
        target_speaker: str | None,
        active_section: str | None,
    ) -> list[str]:
        if target_speaker and target_speaker in team_ids:
            return [target_speaker]

        mentions = [m.lower() for m in MENTION_RE.findall(message)]
        resolved = []
        for mention in mentions:
            for tid in team_ids:
                member = COMMITTEE_MEMBERS.get(tid, {})
                if mention in (tid, member.get("name", "").lower(), member.get("agent_id", "")):
                    resolved.append(tid)
        if resolved:
            return list(dict.fromkeys(resolved))[:3]

        section_map = {
            "market": ["marketing", "accounting"],
            "mvp": ["spec", "dev_app", "dev_gaming"],
            "feasibility": ["spec", "dev_app"],
            "business_case": ["accounting", "pm"],
            "risks": ["spec", "pm"],
            "social_strategy": ["content", "marketing"],
            "visual_identity": ["content", "marketing"],
            "lore": ["game_director", "content"],
            "manufacturing": ["hardware", "embedded_dev"],
        }
        if active_section and active_section in section_map:
            picks = [p for p in section_map[active_section] if p in team_ids]
            if picks:
                return picks[:3]

        for pattern, candidates in KEYWORD_ROUTING:
            if pattern.search(message):
                picks = [c for c in candidates if c in team_ids]
                if picks:
                    return picks[:3]

        default = ["pm"] + [t for t in team_ids if t != "pm"][:2]
        return default[:3]

    def _member_reply(
        self,
        member_id: str,
        dossier_context: str,
        history: list[dict[str, Any]],
        user_message: str,
    ) -> str:
        transcript = []
        for msg in history[-14:]:
            speaker = msg.get("speaker", "?")
            if speaker == "system":
                continue
            label = member_label(speaker) if speaker in COMMITTEE_MEMBERS else speaker
            transcript.append(f"{label}: {msg.get('content', '')[:500]}")
        transcript.append(f"Emilie: {user_message}")

        member = COMMITTEE_MEMBERS.get(member_id, {})
        user = (
            f"Historique récent du comité :\n\n"
            + "\n\n".join(transcript)
            + f"\n\nRéponds maintenant en tant que {member.get('name', member_id)} "
            f"({member.get('title', '')}). Une seule intervention."
        )
        try:
            return self.llm.complete(
                build_member_system(member_id, dossier_context),
                user,
                agent_id=member.get("agent_id", "pm"),
                temperature=0.55,
                max_tokens=400,
            ).strip()
        except Exception as exc:
            logger.warning("committee reply %s failed: %s", member_id, exc)
            return ""

    def _generate_synthesis(
        self, dossier: RndDossierOut, history: list[dict[str, Any]]
    ) -> str:
        lines = []
        for msg in history:
            if msg.get("role") == "user" or msg.get("speaker") in COMMITTEE_MEMBERS:
                lines.append(f"{msg.get('speaker')}: {msg.get('content', '')[:600]}")
        transcript = "\n\n".join(lines[-30:])
        user = (
            f"Dossier : {dossier.title}\n\n"
            f"Transcript comité :\n{transcript}\n\n"
            "Rédige une **synthèse de clôture** markdown pour Emilie :\n"
            "## Décisions\n## Points ouverts\n## Prochaines actions (3 max)\n"
            "## Recommandation GO / MAYBE / NO pour le CEO"
        )
        try:
            return self.llm.complete(
                build_member_system("pm", self._dossier_context(dossier)),
                user,
                agent_id="pm",
                temperature=0.4,
                max_tokens=1200,
            ).strip()
        except Exception as exc:
            logger.warning("committee synthesis failed: %s", exc)
            return "## Synthèse\n\nComité clos — relis le transcript pour les décisions."

    def _apply_synthesis_to_sections(
        self,
        dossier_id: str,
        dossier: RndDossierOut,
        synthesis_md: str,
    ) -> list[str]:
        placeholders = (
            "à compléter lors du comité",
            "identifier en comité",
            "_à compléter",
        )
        committee_sections = [
            "social_strategy",
            "visual_identity",
            "lore",
            "manufacturing",
            "risks",
        ]
        updated: list[str] = []
        for sec in dossier.sections:
            if sec.section_key not in committee_sections:
                continue
            blob = sec.content_md.lower()
            if not any(p in blob for p in placeholders):
                continue
            try:
                content = self._draft_section_from_synthesis(
                    sec.section_key,
                    sec.title,
                    dossier,
                    synthesis_md,
                )
                if content:
                    self.repo.update_section_content(
                        dossier_id,
                        sec.section_key,
                        content,
                        status="under_review",
                    )
                    updated.append(sec.section_key)
            except Exception as exc:
                logger.warning("committee section %s failed: %s", sec.section_key, exc)
        return updated

    def _draft_section_from_synthesis(
        self,
        section_key: str,
        title: str,
        dossier: RndDossierOut,
        synthesis_md: str,
    ) -> str:
        user = (
            f"Section à rédiger : {title} ({section_key})\n"
            f"Dossier : {dossier.title}\n\n"
            f"Synthèse comité :\n{synthesis_md}\n\n"
            "Rédige la section en markdown (150-300 mots), concrète, sans fluff."
        )
        member_id = {
            "social_strategy": "content",
            "visual_identity": "content",
            "lore": "game_director",
            "manufacturing": "hardware",
            "risks": "spec",
        }.get(section_key, "pm")
        return self.llm.complete(
            build_member_system(member_id, self._dossier_context(dossier)),
            user,
            agent_id=COMMITTEE_MEMBERS.get(member_id, {}).get("agent_id", "pm"),
            temperature=0.45,
            max_tokens=900,
        ).strip()
