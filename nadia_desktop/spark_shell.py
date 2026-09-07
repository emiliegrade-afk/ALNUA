"""Spark desktop shell — WebView2 UI (maquette) + HubBridge (Nadia)."""

from __future__ import annotations

import logging
import sys
import threading
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

logger = logging.getLogger("spark.shell")

WEB_DIR = Path(__file__).resolve().parent / "ui" / "spark_web"
INDEX = WEB_DIR / "index.html"


class SparkApi:
    """Exposed to JS as window.pywebview.api."""

    def __init__(self) -> None:
        from core.hub_bridge import HubBridge
        from core.voice import Speaker
        from nadia_config import TTS_BACKEND, TTS_PITCH, TTS_RATE, TTS_VOICE

        self.bridge = HubBridge()
        self.speaker = Speaker(
            backend=TTS_BACKEND,
            voice=TTS_VOICE,
            rate=TTS_RATE,
            pitch=TTS_PITCH,
        )
        self._mic = False

    def chat(
        self,
        message: str,
        deep_search: bool = True,
        pc_access: bool = True,
        attachment: str | None = None,
    ) -> str:
        bits: list[str] = []
        if deep_search:
            bits.append("[Deep Search ON]")
        if pc_access:
            bits.append("[PC Access ON]")
        if attachment:
            bits.append(f"[Fichier joint: {attachment}]")
        payload = (" ".join(bits) + "\n" + message) if bits else message
        self.speaker.stop()
        try:
            reply = self.bridge.chat(payload)
        except Exception as exc:
            logger.exception("chat failed")
            return f"Une erreur s'est produite : {exc}"
        if reply:
            threading.Thread(
                target=self._speak_overlay, args=(reply,), daemon=True
            ).start()
        return reply or ""

    def _speak_overlay(self, facts: str) -> None:
        """Speak overlay only — never the full on-screen reply (DEC-033 Lot 2)."""
        line = None
        try:
            from nadia_config import HUB_ROOT

            hub = str(HUB_ROOT)
            if hub not in sys.path:
                sys.path.insert(0, hub)
            from services.voice_overlay import spoken_overlay

            line = spoken_overlay(facts, agent_id="secretary")
        except Exception:
            logger.warning("desk overlay failed", exc_info=True)
            line = "C'est à l'écran."
        if line:
            self.speaker.speak(line)

    def pick_file(self) -> dict | None:
        try:
            import webview

            window = webview.windows[0] if webview.windows else None
            if not window:
                return None
            paths = window.create_file_dialog(webview.OPEN_DIALOG)
            if not paths:
                return None
            path = str(paths[0])
            name = path.replace("\\", "/").rsplit("/", 1)[-1]
            return {"path": path, "name": name}
        except Exception as exc:
            logger.warning("pick_file: %s", exc)
            return None

    def toggle_mic(self) -> bool:
        self._mic = not self._mic
        return self._mic


def run() -> int:
    from nadia_config import PRODUCT_NAME, WINDOW_HEIGHT, WINDOW_TITLE, WINDOW_WIDTH

    if not INDEX.is_file():
        logger.error("UI manquante: %s", INDEX)
        return 1

    try:
        import webview
    except ImportError:
        logger.error("pywebview requis: pip install pywebview")
        return 1

    api = SparkApi()
    icon = Path(__file__).resolve().parent.parent / "assets" / "alnua-x-round.ico"
    webview.create_window(
        WINDOW_TITLE or PRODUCT_NAME,
        url=INDEX.as_uri(),
        js_api=api,
        width=WINDOW_WIDTH,
        height=WINDOW_HEIGHT,
        min_size=(1024, 700),
        background_color="#0B0C0F",
        confirm_close=False,
    )
    kwargs: dict = {"gui": "edgechromium"} if sys.platform == "win32" else {}
    if icon.exists():
        kwargs["icon"] = str(icon)
    webview.start(**kwargs)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    raise SystemExit(run())
