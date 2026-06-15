"""Diagnostic Telegram + investigation R&D flow."""
from __future__ import annotations

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")

from config.settings import get_settings
from agents.coo_agent import COOAgent
from services.coo_telegram_intents import (
    detect_rnd_investigation,
    extract_investigation_query,
    launch_rnd_investigation,
    _run_investigation_worker,
)
from skills.skill_telegram_notify import notify_telegram


def main() -> None:
    settings = get_settings()
    print("TELEGRAM_BOT_TOKEN:", "OK" if settings.telegram_bot_token else "MISSING")
    print("TELEGRAM_CHAT_ID:", repr(settings.telegram_chat_id))

    msg = "demande au R&D d'investiguer sur le VPN russse trending"
    print("\n--- intent ---")
    print("detect:", detect_rnd_investigation(msg))
    print("topic:", extract_investigation_query(msg))

    print("\n--- COO immediate ack ---")
    t0 = time.time()
    ack = COOAgent().handle_instruction(msg)
    print(f"({time.time() - t0:.2f}s)", ack[:400])

    print("\n--- notify_telegram ping ---")
    ok = notify_telegram("🧪 Test diagnostic Hub — si tu vois ce message, notify_telegram OK.")
    print("notify_telegram:", ok)

    if "--full" in sys.argv:
        print("\n--- full investigation (blocking, may take 1-3 min) ---")
        topic = extract_investigation_query(msg) or "VPN russe trending"
        _run_investigation_worker(topic)
        print("done")


if __name__ == "__main__":
    main()
