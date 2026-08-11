"""Secretary agent — ops NL handlers (research, wake, Aria, conversation)."""
from __future__ import annotations

import logging

from skills.skill_agent_learning import inject_learning_context

logger = logging.getLogger(__name__)


class SecretaryHandlersOpsMixin:
    """Requires ``SecretaryInstructionMixin._finish_instruction`` and ``AgentBase``."""

    @staticmethod
    def _telegram_chat_id(session_id: str) -> int | None:
        if not session_id.startswith("tg:"):
            return None
        try:
            return int(session_id.split(":", 1)[1])
        except (ValueError, IndexError):
            return None

    def _handle_research(self, instruction: str, *, session_id: str = "hub") -> str:
        from agents.coo_agent import _detect_research_intent, _extract_research_topic
        from services.bureau_library import generate_ceo_report, run_bureau_research
        from services.secretary_intents import extract_research_query

        chat_id = self._telegram_chat_id(session_id)
        is_telegram = chat_id is not None

        query = extract_research_query(instruction)
        if query == "__report__":
            report = generate_ceo_report(days=7)
            out = report.get("markdown") or report.get("executive_summary", "Rapport généré.")
            self._finish_instruction(instruction, out[:200])
            return out

        is_research, research_agent = _detect_research_intent(instruction)
        if is_research and research_agent == "rnd_agent":
            topic = _extract_research_topic(instruction, research_agent) or query
            if topic and len(topic) >= 4:
                from services.coo_telegram_intents import launch_rnd_investigation

                out = launch_rnd_investigation(topic, chat_id=chat_id)
                self._finish_instruction(instruction, out[:200])
                return out

        lower = instruction.lower()
        if any(k in lower for k in ("deep research", "recherche profonde", "approfond")):
            try:
                from services.deep_research import quick_research

                report = quick_research(query, agent_id="secretary")
                if isinstance(report, dict):
                    summary = (
                        report.get("executive_summary")
                        or report.get("summary")
                        or str(report)[:2000]
                    )
                else:
                    summary = str(report)[:2000]
                out = f"🔬 **Recherche approfondie** — « {query} »\n\n{summary}"
                self._finish_instruction(instruction, out[:200])
                return out
            except Exception as exc:
                logger.warning("deep research fallback: %s", exc)

        result = run_bureau_research(
            query,
            requested_by="nadia",
            blocking=not is_telegram,
            notify_chat_id=chat_id,
        )
        if not is_telegram and result.get("entries_saved") is not None:
            n = result.get("entries_saved", 0)
            out = (
                f"📚 **Recherche terminée** — « {query} »\n\n"
                f"**{n}** fiche(s) archivée(s) dans la bibliothèque.\n"
                "Rien n'a été supprimé — consulte **Bibliothèque** dans le Hub."
            )
        else:
            out = (
                f"📚 **Recherche lancée** — « {query} »\n\n"
                f"{result.get('message', '')}\n\n"
                + (
                    "Je t'enverrai le bilan ici dès que c'est prêt (~1-3 min)."
                    if is_telegram
                    else "Tout est archivé dans la bibliothèque. "
                    "Demande « rapport bibliothèque » pour un résumé CEO."
                )
            )
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_wake_ops(self, instruction: str) -> str:
        from services.agent_wake import wake_agents

        result = wake_agents(notify=False, retry_failed=True)
        summary = result.get("summary", "")
        out = (
            "✅ **Pipeline Academy relancé** — Théo (dev_app) reprend les exercices en file.\n\n"
            f"{summary}"
        )
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_aria_delegation(self, instruction: str) -> str:
        from agents.coo_agent import COOAgent
        from services.secretary_intents import extract_aria_delegation_message

        payload = extract_aria_delegation_message(instruction)
        try:
            response = COOAgent(self.db).handle_instruction(payload)
        except Exception:
            response = (
                "Aria est indisponible pour l'instant — vérifie que le bot COO tourne "
                "(@Alnua_coo_bot) ou que le Hub API est démarré."
            )
        out = f"📨 **Transmis à Aria** :\n\n{response}"
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_ask_lawyer(self, instruction: str, *, session_id: str = "hub") -> str:
        """Escalate to enterprise legal counsel (separate agent)."""
        try:
            from agents.legal_counsel_agent import LegalCounselAgent
            from services.input_sanitizer import sanitize_user_input

            clean = sanitize_user_input(instruction, max_length=4000, redact_pii_enabled=False)
            result = LegalCounselAgent().advise(clean, regions=["UE", "USA", "ASIE"])
            body = result.get("advice") or result.get("summary") or str(result)
            out = (
                "⚖️ **Nadia → Avocat d'entreprise ALNUA**\n\n"
                f"{body}\n\n"
                "_Avis d'aide à la décision — pas un conseil juridique opposable. "
                "Fais valider avant signature._"
            )
        except Exception as exc:
            logger.warning("ask_lawyer failed: %s", exc)
            out = (
                "Je n'ai pas pu joindre l'avocat d'entreprise pour l'instant. "
                "Reformule ta question juridique ou réessaie dans un instant."
            )
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_write_doc(self, instruction: str, *, session_id: str = "hub") -> str:
        from services.input_sanitizer import sanitize_user_input
        from services.nadia_docs import create_document, list_documents

        clean = sanitize_user_input(instruction, max_length=4000, redact_pii_enabled=False)
        # Ask LLM for title + body quickly
        prompt = (
            f"Emilie demande un document : {clean}\n\n"
            'JSON : {"title":"...","content":"markdown complet","doc_type":"note|contrat|cr"}'
        )
        try:
            raw = self._complete(prompt, temperature=0.4, max_tokens=4000)
            from agents.base import parse_json_response

            data = parse_json_response(raw)
            if not isinstance(data, dict):
                raise ValueError("bad json")
            entry = create_document(
                str(data.get("title") or "Document Nadia"),
                str(data.get("content") or clean),
                doc_type=str(data.get("doc_type") or "note"),
            )
        except Exception:
            entry = create_document("Note Nadia", f"# Note\n\n{clean}\n", doc_type="note")
        docs = list_documents()[:5]
        out = (
            f"📝 **Document créé** — « {entry.get('title')} »\n"
            f"Fichier : `{entry.get('path')}`\n"
            f"ID : `{entry.get('id')}` — éditable dans Nadia Desktop / data/nadia_docs.\n"
            f"Docs récents : {', '.join(d.get('title', '') for d in docs)}"
        )
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_housekeep(self, instruction: str, *, session_id: str = "hub") -> str:
        from agents.housekeeper_agent import HousekeeperAgent

        agent = HousekeeperAgent()
        lower = instruction.lower()
        if "quarantaine" in lower or "supprim" in lower:
            st = agent.status()
            out = (
                f"🧹 **Quarantaine** : {st.get('quarantine_count', 0)} élément(s)\n"
                f"Dossier : `{st.get('quarantine_dir')}`\n"
                "Dis les chemins exacts à mettre en quarantaine, ou demande un scan/propose d'abord."
            )
        elif "applique" in lower or "déplace" in lower or "deplace" in lower:
            result = agent.apply(dry_run=False)
            n = len(result.get("moves") or [])
            out = (
                f"🧹 **Déplacements** : {n} fichier(s)\n"
                f"Rapport : `{result.get('report_path')}`\n"
                f"Erreurs : {len(result.get('errors') or [])}"
            )
        elif "propos" in lower:
            result = agent.propose()
            n = len(result.get("proposals") or [])
            out = (
                f"🧹 **Proposition de rangement** : {n} fichier(s)\n"
                f"Rapport : `{result.get('report_path')}`\n"
                "Rien n'a été déplacé. Dis « applique le rangement » pour exécuter."
            )
        else:
            result = agent.scan()
            out = (
                f"🧹 **Scan PC** : {result.get('count', 0)} éléments sur "
                f"{len(result.get('roots') or [])} racines\n"
                f"Racines : {', '.join(result.get('roots') or [])}\n"
                "Dis « propose un rangement » pour un plan, ou donne des chemins extra."
            )
        self._finish_instruction(instruction, out[:200])
        return out

    def _handle_conversation(
        self,
        instruction: str,
        *,
        chat_id: int | str | None = None,
    ) -> str:
        from services.secretary_intents import build_academy_status_brief
        from services.telegram_chat_memory import get_context_block
        from services.telegram_presence import CANNOT_DO_NADIA, hub_online

        context = build_academy_status_brief()
        history = get_context_block(chat_id)
        hub_line = "Hub en ligne." if hub_online() else "Hub ARRÊTÉ — pas de pipeline ni actions lourdes."

        prompt = inject_learning_context(
            f"""Emilie t'écrit en langage naturel :
{instruction}

{history}

Contexte ALNUA (indicatif, pas obligatoire à réciter) :
{context}
État technique : {hub_line}

Tu es Nadia Faure — assistante personnelle d'Emilie (CEO ALNUA), niveau ChatGPT/Claude
branchée sur le Hub : tu comprends le langage naturel, tu aides sur tout sujet utile
(organisation, rédaction, idées, explications, planning, mails, contrats, recherches).
Tu tutoies Emilie. Français clair, chaleureux, concret. 3 à 12 phrases selon le besoin.

Règles :
- Ne demande PAS de « mots magiques » (pipeline, academy…). Comprends la paraphrase.
- Si une action Hub précise est requise (envoyer un mail, relancer Théo, ouvrir l'agenda),
  dis ce que tu peux faire et propose la prochaine étape concrète.
- Ops stratégiques lourdes / multi-pôles → propose de transmettre à Aria (COO).
- Questions juridiques / contrats à valider avant signature → propose l'avocat d'entreprise ALNUA.
- Si tu ne sais pas : dis-le et pose UNE question précise.
- Pas de JSON — texte direct.""",
            self.AGENT_NAME,
            instruction[:80],
        )
        try:
            raw = self._complete(prompt, temperature=0.5)
            text = (raw or "").strip()
            if not text:
                text = CANNOT_DO_NADIA
        except Exception as exc:
            logger.warning("secretary conversation failed: %s", exc)
            text = (
                "Je n'ai pas pu formuler une réponse (connexion IA ou Hub).\n\n"
                + CANNOT_DO_NADIA
            )
        self._finish_instruction(instruction, text)
        return text
