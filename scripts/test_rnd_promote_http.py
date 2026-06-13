"""HTTP smoke test for POST /rnd/ideas/{id}/promote."""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE = os.getenv("HUB_API_URL", "http://localhost:8000").rstrip("/")
KEY = os.getenv("HUB_API_KEY", "").strip()
HEADERS = {"X-Hub-Key": KEY} if KEY else {}


def main() -> int:
    try:
        health = requests.get(f"{BASE}/health", timeout=5)
        print(f"health {health.status_code}")
    except Exception as exc:
        print(f"BACKEND DOWN: {exc}")
        print("Lance: uvicorn api.main:app --host 0.0.0.0 --port 8000")
        return 1

    ideas = requests.get(f"{BASE}/rnd/ideas?limit=10", headers=HEADERS, timeout=15).json()
    target = next((i for i in ideas if not i.get("dossier_id")), None)
    if not target:
        print("SKIP — toutes les idées ont déjà un dossier")
        dossiers = requests.get(f"{BASE}/rnd/dossiers?limit=3", headers=HEADERS, timeout=15).json()
        print(f"OK dossiers list ({len(dossiers)} items)")
        return 0

    print(f"promote {target['id']} ({target['title'][:40]})")
    t0 = time.time()
    resp = requests.post(
        f"{BASE}/rnd/ideas/{target['id']}/promote",
        headers=HEADERS,
        timeout=30,
    )
    elapsed = round(time.time() - t0, 2)
    print(f"status {resp.status_code} in {elapsed}s")
    if not resp.ok:
        print(resp.text[:400])
        return 1

    data = resp.json()
    assert data.get("dossier", {}).get("slug")
    enriching = data.get("enriching")
    print(f"OK slug={data['dossier']['slug']} enriching={enriching}")
    if enriching is not True:
        print("WARN: enriching!=True — redémarre uvicorn si le code vient d'être mis à jour")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
