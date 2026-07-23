"""
hub_bridge.py — Pont entre Nadia Desktop et ALNUA Hub.

Importe SecretaryAgent directement depuis le Hub (même process, même venv).
Si le Hub est introuvable → fallback LLM local transparent.
"""

from __future__ import annotations

import logging
import sys
from typing import TYPE_CHECKING

from nadia_config import HUB_ROOT, OLLAMA_MODEL, OLLAMA_URL, SESSION_ID

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# ── Injection du Hub dans le path Python ────────────────────────────────────

def _inject_hub_path() -> bool:
    """Ajoute le Hub au sys.path si ce n'est pas déjà fait."""
    hub = str(HUB_ROOT)
    if hub not in sys.path:
        sys.path.insert(0, hub)
    return HUB_ROOT.exists()


# ── Chargement de SecretaryAgent ────────────────────────────────────────────

class HubBridge:
    """Pont vers SecretaryAgent du Hub."""

    def __init__(self) -> None:
        self._agent = None
        self._mode  = "offline"
        self._init()

    def _init(self) -> None:
        if not _inject_hub_path():
            logger.warning("Hub introuvable à %s — mode offline", HUB_ROOT)
            return

        try:
            from agents.secretary_agent import SecretaryAgent  # type: ignore
            self._agent = SecretaryAgent()
            self._mode  = "hub"
            logger.info("✅ SecretaryAgent Hub chargé")
        except ImportError as e:
            logger.warning("Import Hub échoué (%s) — tentative GLM direct", e)
            self._mode = "glm_direct"
        except Exception as e:
            logger.error("Erreur init Hub : %s", e)
            self._mode = "offline"

    # ── Point d'entrée principal ─────────────────────────────────────────────

    def chat(self, message: str) -> str:
        """
        Envoie un message à Nadia et retourne sa réponse.
        Routing automatique : Hub → GLM direct → Ollama → offline.
        """
        if not message.strip():
            return ""

        if self._mode == "hub" and self._agent:
            try:
                return self._agent.handle_instruction(
                    message, session_id=SESSION_ID
                )
            except Exception as e:
                logger.error("Hub error : %s — fallback", e)
                self._mode = "glm_direct"

        if self._mode == "glm_direct":
            return self._chat_glm(message)

        return self._chat_ollama(message)

    # ── Fallback GLM-5.2 direct ──────────────────────────────────────────────

    def _chat_glm(self, message: str) -> str:
        try:
            from nadia_config import GLM_API_KEY, GLM_BASE_URL, GLM_MODEL
            if not GLM_API_KEY:
                self._mode = "ollama"
                return self._chat_ollama(message)

            from openai import OpenAI
            client = OpenAI(api_key=GLM_API_KEY, base_url=GLM_BASE_URL)
            resp = client.chat.completions.create(
                model=GLM_MODEL,
                messages=[
                    {"role": "system", "content": _NADIA_SYSTEM_PROMPT},
                    {"role": "user",   "content": message},
                ],
                temperature=0.5,
                max_tokens=1024,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            logger.error("GLM error : %s — fallback Ollama", e)
            self._mode = "ollama"
            return self._chat_ollama(message)

    # ── Fallback Ollama local ────────────────────────────────────────────────

    def _chat_ollama(self, message: str) -> str:
        try:
            import requests
            payload = {
                "model": OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": _NADIA_SYSTEM_PROMPT},
                    {"role": "user",   "content": message},
                ],
                "stream": False,
            }
            r = requests.post(
                f"{OLLAMA_URL}/api/chat",
                json=payload,
                timeout=60,
            )
            r.raise_for_status()
            return r.json()["message"]["content"]
        except Exception as e:
            logger.error("Ollama error : %s", e)
            return (
                "Je suis déconnectée du Hub et du LLM local pour l'instant. "
                "Vérifie qu'Ollama tourne ou que le Hub est démarré."
            )

    @property
    def mode(self) -> str:
        return self._mode


# ── Persona Nadia (fallback quand le Hub n'est pas dispo) ───────────────────

_NADIA_SYSTEM_PROMPT = """Tu es Nadia Faure, secrétaire de direction d'ALNUA.
Tu travailles directement avec Emilie, la CEO.
Tu es professionnelle, chaleureuse, efficace. Tu tutoies Emilie.
Tu gères : emails, agenda, contrats, comptes rendus, délégation aux autres agents.
Réponds en français, 3 à 8 phrases max sauf si un document long est demandé.
Si tu ne peux pas faire quelque chose, dis-le clairement et propose une alternative.

Quand la réponse sera lue à voix haute (desktop) :
- pas de markdown, puces, emojis ni smileys
- pas d'URL ni de codes techniques
- phrases courtes, naturelles, comme à l'oral"""
