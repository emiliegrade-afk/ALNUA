#!/usr/bin/env python3
"""Sprint B — post-deploy smoke checks (API + optional Vercel web)."""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def _hub_key() -> str:
    from config.settings import get_settings

    get_settings.cache_clear()
    key = os.environ.get("HUB_API_KEY") or get_settings().hub_api_key
    if not key:
        raise SystemExit("HUB_API_KEY missing — set in .env or environment")
    return key


def check_api(base: str, hub_key: str) -> list[str]:
    base = base.rstrip("/")
    headers = {"X-Hub-Key": hub_key}
    errors: list[str] = []

    try:
        with httpx.Client(timeout=20.0) as client:
            health = client.get(f"{base}/health")
            if health.status_code != 200:
                errors.append(f"GET /health → {health.status_code}")
            else:
                print(f"OK  GET {base}/health")

            flags = client.get(f"{base}/admin/flags", headers=headers)
            if flags.status_code != 200:
                errors.append(f"GET /admin/flags → {flags.status_code}")
            else:
                body = flags.json()
                for name in (
                    "admin_costs_page_enabled",
                    "gdd_manager_enabled",
                    "briefing_coo_section_enabled",
                ):
                    val = body.get(name)
                    status = "OK " if val else "WARN"
                    print(f"{status}  flag {name}={val}")
                    if not val and body.get("environment") == "production":
                        errors.append(f"flag {name} is false in production")

            costs = client.get(f"{base}/services/costs/report?days=1", headers=headers)
            if costs.status_code != 200:
                errors.append(f"GET /services/costs/report → {costs.status_code}")
            else:
                print(f"OK  GET {base}/services/costs/report")
    except httpx.ConnectError as exc:
        errors.append(f"cannot reach {base} ({exc})")
        if "alnua.com" in base:
            print(
                "\nHint: api.alnua.com has no DNS yet (or VPS/nginx not up).\n"
                "  Pre-deploy:  npm run deploy:verify -- --api http://127.0.0.1:8000\n"
                "  Post-DNS:    set HUB_API_URL=https://api.alnua.com && npm run deploy:verify"
            )

    return errors


def check_web(web_url: str, hub_key: str) -> list[str]:
    web_url = web_url.rstrip("/")
    errors: list[str] = []
    headers = {"X-Hub-Key": hub_key}

    with httpx.Client(timeout=30.0, follow_redirects=True) as client:
        for path in ("/", "/briefing", "/admin"):
            res = client.get(f"{web_url}{path}")
            if res.status_code != 200:
                errors.append(f"GET {path} → {res.status_code}")
            else:
                print(f"OK  GET {web_url}{path}")

        proxy = client.get(f"{web_url}/api/hub/admin/flags", headers=headers)
        if proxy.status_code != 200:
            errors.append(f"GET /api/hub/admin/flags → {proxy.status_code}")
        else:
            print(f"OK  GET {web_url}/api/hub/admin/flags (proxy)")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Sprint B deploy verification")
    parser.add_argument(
        "--api",
        default=os.environ.get("HUB_API_URL") or "http://127.0.0.1:8002",
        help="API base URL (default: HUB_API_URL env or http://127.0.0.1:8002)",
    )
    parser.add_argument(
        "--web",
        default=os.environ.get("BETA_PORTAL_BASE_URL", ""),
        help="Vercel app URL (optional)",
    )
    args = parser.parse_args()
    hub_key = _hub_key()

    print(f"=== API checks ({args.api}) ===")
    errors = check_api(args.api, hub_key)

    if args.web:
        print(f"\n=== Web checks ({args.web}) ===")
        errors.extend(check_web(args.web, hub_key))

    if errors:
        print("\nFAILED:")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("\nAll Sprint B checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
