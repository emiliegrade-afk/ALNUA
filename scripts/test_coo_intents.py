"""Quick smoke test for COO Telegram intents."""
from services.coo_telegram_intents import (
    detect_idea_capture,
    detect_rnd_investigation,
    extract_idea_text,
    extract_investigation_query,
)

CASES = [
    "demande au R&D d'investiguer sur le VPN russse trending",
    "recherche pour r&d VPN privacy market",
    "note cette idée: app vanlife offline",
    "j'ai une idée pour capteur IoT van",
]

for msg in CASES:
    print("---", msg)
    print("  inv:", detect_rnd_investigation(msg), "->", extract_investigation_query(msg))
    print("  idea:", detect_idea_capture(msg), "->", extract_idea_text(msg))
