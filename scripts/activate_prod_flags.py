#!/usr/bin/env python3
"""Append Phase 1-3 flags to .env.prod for VPS (Sprint B)."""
from __future__ import annotations

from pathlib import Path

FLAGS = """
# --- Phase 1-3 activation (production) ---
ENVIRONMENT=production
ADMIN_COSTS_PAGE_ENABLED=1
ADMIN_EVENTS_PAGE_ENABLED=1
ADMIN_AB_TEST_PAGE_ENABLED=1
BRIEFING_COO_SECTION_ENABLED=1
GDD_MANAGER_ENABLED=1
HUB_API_URL=https://api.alnua.com
BETA_PORTAL_BASE_URL=https://app.alnua.com
""".strip()

MARKER = "# --- Phase 1-3 activation"


def main() -> int:
    env_path = Path(__file__).resolve().parent.parent / ".env.prod"
    if not env_path.exists():
        example = Path(__file__).resolve().parent.parent / "deploy" / ".env.prod.example"
        if example.exists():
            env_path.write_text(example.read_text(encoding="utf-8") + "\n", encoding="utf-8")
            print(f"Created {env_path} from deploy/.env.prod.example")
        else:
            print(f"ERROR: {env_path} missing — copy deploy/.env.prod.example first.")
            return 1

    text = env_path.read_text(encoding="utf-8")
    if MARKER in text:
        print(".env.prod already has Phase 1-3 activation block.")
        return 0

    if not text.endswith("\n"):
        text += "\n"
    env_path.write_text(text + "\n" + FLAGS + "\n", encoding="utf-8")
    print("Added production flags to .env.prod — restart: docker compose restart hub_api")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
