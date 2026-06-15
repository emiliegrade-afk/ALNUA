#!/usr/bin/env python3
"""Append Phase 1-3 feature flags to .env if missing (activation step A.2)."""
from __future__ import annotations

from pathlib import Path

FLAGS = """
# --- Phase 1-3 activation (gap remediation) ---
ADMIN_COSTS_PAGE_ENABLED=1
ADMIN_EVENTS_PAGE_ENABLED=1
ADMIN_AB_TEST_PAGE_ENABLED=1
BRIEFING_COO_SECTION_ENABLED=1
GDD_MANAGER_ENABLED=1
""".strip()

MARKER = "# --- Phase 1-3 activation"


def main() -> int:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        print(f"ERROR: {env_path} missing — copy from .env.example first.")
        return 1

    text = env_path.read_text(encoding="utf-8")
    if MARKER in text:
        print(".env already has Phase 1-3 activation flags.")
        return 0

    if not text.endswith("\n"):
        text += "\n"
    env_path.write_text(text + "\n" + FLAGS + "\n", encoding="utf-8")
    print("Added Phase 1-3 flags to .env — restart API + web.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
