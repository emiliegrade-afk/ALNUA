#!/usr/bin/env python3
"""Audit readiness beta NUAWAY — Super Plan Phase 6."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def main() -> int:
    from services.nuaway_readiness import generate_readiness_report

    print("=" * 60)
    print("ALNUA — NUAWAY Beta Readiness Audit (Phase 6)")
    print("=" * 60)

    report = generate_readiness_report(refresh_gate=True)
    print(f"\n{report.get('headline')}\n")
    print(f"Beta ready : {'OUI' if report.get('beta_ready') else 'NON'}")
    print(
        f"Score : {report.get('readiness_pct')}% "
        f"({report.get('passed')}/{report.get('total')})"
    )
    print(f"Critiques : {report.get('critical_passed')}/{report.get('critical_total')}\n")

    for c in report.get("criteria") or []:
        mark = "OK " if c.get("passed") else "NO "
        crit = " *" if c.get("critical") else ""
        print(f"  [{mark}] {c.get('label')}{crit}")

    missing = report.get("missing_critical") or []
    if missing:
        print("\nBloquants :")
        for m in missing:
            print(f"  - {m}")

    print("\n" + (report.get("markdown") or "")[:1200])
    print("\n" + "=" * 60)
    return 0 if report.get("beta_ready") else 1


if __name__ == "__main__":
    raise SystemExit(main())
