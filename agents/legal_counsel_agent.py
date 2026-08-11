"""Legal Counsel Agent — enterprise lawyer (UE / USA / Asia), independent from Nadia."""

from __future__ import annotations

from typing import Any

from agents.agent_base import AgentBase
from agents.base import log_agent_action, parse_json_response
from config.agent_operating_spec import get_system_prompt
from services.input_sanitizer import sanitize_user_input
from skills.skill_agent_learning import inject_learning_context, record_task_learning
from skills.skill_langfuse import trace_agent

_DISCLAIMER = (
    "Aide à l'analyse juridique — pas un avocat inscrit au barreau ni un conseil "
    "juridique opposable. Faire valider par un conseil humain avant signature."
)


class LegalCounselAgent(AgentBase):
    AGENT_NAME = "legal_counsel"
    SYSTEM_PROMPT = get_system_prompt("legal_counsel")

    @trace_agent("legal_counsel")
    def advise(
        self,
        question: str,
        *,
        regions: list[str] | None = None,
        context: str = "",
    ) -> dict[str, Any]:
        """General enterprise-law advice across regions."""
        regions = regions or ["UE", "USA", "ASIE"]
        q = sanitize_user_input(question, max_length=4000, redact_pii_enabled=False)
        ctx = sanitize_user_input(context, max_length=3000, redact_pii_enabled=False)
        prompt = inject_learning_context(
            f"""Question juridique d'Emilie (CEO ALNUA) :
{q}

Régions à couvrir : {", ".join(regions)}
Contexte additionnel : {ctx or "aucun"}

Tu es l'avocat d'entreprise ALNUA (droit des affaires international).
Couvre : contrats, corporate, IP, pub/influence, data/privacy, RH light, litiges early-risk.
Pour chaque région pertinente : points de vigilance, écarts typiques UE↔USA↔Asie.

JSON :
{{
  "summary": "synthèse 2-4 phrases",
  "advice": "texte clair pour Emilie",
  "risks": ["..."],
  "by_region": {{"UE": "...", "USA": "...", "ASIE": "..."}},
  "next_steps": ["..."],
  "disclaimer": "{_DISCLAIMER}"
}}""",
            self.AGENT_NAME,
            q[:80],
        )
        raw = self._complete(prompt, temperature=0.25, max_tokens=4000)
        result = parse_json_response(raw)
        if not isinstance(result, dict):
            result = {"summary": str(raw)[:500], "advice": str(raw)[:2000]}
        result.setdefault("disclaimer", _DISCLAIMER)
        log_agent_action(
            self.db,
            self.AGENT_NAME,
            "advise",
            input_summary=q[:120],
            output_summary=str(result.get("summary", ""))[:160],
        )
        try:
            record_task_learning(self.AGENT_NAME, "advise", str(result.get("summary", ""))[:300], True)
        except Exception:
            pass
        return result

    @trace_agent("legal_counsel")
    def review_document(
        self,
        document_text: str,
        *,
        doc_kind: str = "contrat",
        regions: list[str] | None = None,
    ) -> dict[str, Any]:
        """Review a draft or received contract/document before sign-off."""
        regions = regions or ["UE", "USA", "ASIE"]
        doc = sanitize_user_input(document_text, max_length=12000, redact_pii_enabled=False)
        prompt = inject_learning_context(
            f"""Relis ce document ({doc_kind}) avant éventuelle signature Emilie / ALNUA.

Document :
\"\"\"
{doc}
\"\"\"

Régions : {", ".join(regions)}

JSON :
{{
  "verdict": "ok_with_caveats|needs_changes|do_not_sign|insufficient_info",
  "summary": "...",
  "red_flags": ["..."],
  "missing_clauses": ["..."],
  "suggested_edits": ["..."],
  "by_region": {{"UE": "...", "USA": "...", "ASIE": "..."}},
  "disclaimer": "{_DISCLAIMER}"
}}""",
            self.AGENT_NAME,
            doc_kind,
        )
        raw = self._complete(prompt, temperature=0.2, max_tokens=5000)
        result = parse_json_response(raw)
        if not isinstance(result, dict):
            result = {"verdict": "insufficient_info", "summary": str(raw)[:500]}
        result.setdefault("disclaimer", _DISCLAIMER)
        log_agent_action(
            self.db,
            self.AGENT_NAME,
            "review_document",
            input_summary=f"{doc_kind}:{len(doc)}c",
            output_summary=str(result.get("verdict", ""))[:80],
        )
        return result

    @trace_agent("legal_counsel")
    def validate_before_sign(
        self,
        document_text: str,
        *,
        regions: list[str] | None = None,
    ) -> dict[str, Any]:
        """CEO gate helper — wraps review_document with explicit sign recommendation."""
        review = self.review_document(document_text, doc_kind="contrat", regions=regions)
        verdict = str(review.get("verdict") or "")
        can_sign = verdict in {"ok_with_caveats"}
        return {
            **review,
            "can_recommend_sign": can_sign,
            "ceo_action": (
                "Peux signer après lecture des caveats"
                if can_sign
                else "Ne pas signer tant que les points rouges / manques ne sont pas traités"
            ),
            "disclaimer": _DISCLAIMER,
        }
