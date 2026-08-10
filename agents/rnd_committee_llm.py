"""R&D committee agent — LLM helpers, routing, section drafting."""
from __future__ import annotations

import logging
import os
from typing import Any

from agents.base import LLMClient, parse_json_response
from agents.rnd_committee_constants import KEYWORD_ROUTING, MENTION_RE
from agents.rnd_committee_prompts import KICKOFF_USER, build_member_system
from services.rnd_committee import COMMITTEE_MEMBERS, member_label
from services.rnd_schemas import RndDossierOut

logger = logging.getLogger(__name__)


class RndCommitteeLlmMixin:
    """Requires ``self.repo``, ``self._complete`` from ``AgentBase``."""

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
            raw = self._complete(
                KICKOFF_USER.format(members=member_ids),
                system_prompt=build_member_system("pm", context),
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
            "Historique récent du comité :\n\n"
            + "\n\n".join(transcript)
            + f"\n\nRéponds maintenant en tant que {member.get('name', member_id)} "
            f"({member.get('title', '')}). Une seule intervention."
        )
        try:
            return self._complete(
                user,
                system_prompt=build_member_system(member_id, dossier_context),
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
            return self._complete(
                user,
                system_prompt=build_member_system("pm", self._dossier_context(dossier)),
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
        return self._complete(
            user,
            system_prompt=build_member_system(member_id, self._dossier_context(dossier)),
            agent_id=COMMITTEE_MEMBERS.get(member_id, {}).get("agent_id", "pm"),
            temperature=0.45,
            max_tokens=900,
        ).strip()
