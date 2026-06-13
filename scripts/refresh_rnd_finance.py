"""Recalculate finance_json for all dossiers (ai_solo model migration)."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.rnd_dossier_agent import RndDossierAgent
from services.rnd_finance_estimate import is_stale_finance
from services.rnd_repository import get_rnd_repository


def main() -> int:
    repo = get_rnd_repository()
    agent = RndDossierAgent(repo)
    dossiers = repo.list_dossiers(limit=100)
    updated = 0
    for d in dossiers:
        full = repo.get_dossier(d.id)
        if not full:
            continue
        if not is_stale_finance(full.finance_json):
            print(f"SKIP {d.slug} — already fresh")
            continue
        try:
            result = agent.estimate_finance(str(d.id))
            fj = result["finance_json"]
            print(
                f"OK {d.slug}: capex {full.finance_json.get('capex_eur') if full.finance_json else '?'} "
                f"-> {fj.get('capex_eur')} | M12 {fj.get('revenue_hypothesis', {}).get('m12_monthly_run_rate_eur')}"
            )
            updated += 1
        except Exception as exc:
            print(f"FAIL {d.slug}: {exc}")
    print(f"\nDone — {updated} dossier(s) refreshed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
