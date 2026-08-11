"""
main.py — Nadia Desktop
Point d'entrée unique.

Lance : python main.py
"""

from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path

# Assure que nadia_desktop/ est dans le path
sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("nadia.main")


def main() -> None:
    from nadia_config import (
        TTS_BACKEND, TTS_PITCH, TTS_RATE, TTS_VOICE, WAKE_WORD,
        WAKE_WORD_ENABLED, WHISPER_LANGUAGE, WHISPER_MODEL,
    )
    from core.hub_bridge import HubBridge
    from core.voice import Speaker, SpeechListener
    from ui.window import NadiaWindow

    # ── 1. Hub Bridge ────────────────────────────────────────────────────────
    bridge = HubBridge()
    logger.info("Mode LLM : %s", bridge.mode)

    # ── 2. TTS ───────────────────────────────────────────────────────────────
    speaker = Speaker(
        backend=TTS_BACKEND,
        voice=TTS_VOICE,
        rate=TTS_RATE,
        pitch=TTS_PITCH,
    )

    # ── 3. Callbacks ─────────────────────────────────────────────────────────
    window_ref: list[NadiaWindow] = []   # accès thread-safe à la fenêtre

    def handle_message(text: str) -> None:
        """Appelé depuis UI thread ou STT thread — toujours thread-safe."""
        def _work():
            try:
                response = bridge.chat(text)
                if window_ref:
                    window_ref[0].push_response(response)
                    speaker.speak(response)
            except Exception as e:
                logger.error("Chat error : %s", e)
                err = "Une erreur s'est produite — vérifie les logs."
                if window_ref:
                    window_ref[0].push_response(err)

        threading.Thread(target=_work, daemon=True).start()

    mic_active = [False]
    listener: list[SpeechListener] = []

    def toggle_mic() -> None:
        mic_active[0] = not mic_active[0]
        if mic_active[0]:
            if not listener:
                l = SpeechListener(
                    on_text=lambda t: window_ref[0].push_stt_text(t) if window_ref else None,
                    model_size=WHISPER_MODEL,
                    language=WHISPER_LANGUAGE,
                    wake_word=WAKE_WORD if WAKE_WORD_ENABLED else None,
                )
                listener.append(l)
                l.start()
                logger.info("🎤 Micro activé")
        else:
            if listener:
                listener[0].stop()
                listener.clear()
                logger.info("🔇 Micro désactivé")

    # ── 4. Fenêtre ───────────────────────────────────────────────────────────
    win = NadiaWindow(
        on_send=handle_message,
        on_mic_toggle=toggle_mic,
        mic_enabled=False,
    )
    win.set_hub_mode(bridge.mode)
    window_ref.append(win)

    # ── 5. Loop ──────────────────────────────────────────────────────────────
    logger.info("🚀 Nadia Desktop démarrée")
    win.run()


if __name__ == "__main__":
    main()
