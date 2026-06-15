#!/usr/bin/env python3
"""
academy_benchmark.py — Mesure la progression et la qualité de l'académie.

Usage:
    python scripts/academy_benchmark.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv

load_dotenv(ROOT / ".env")


def main() -> int:
    from services.academy_curriculum import all_exercises
    from services.academy_progress import get_academy_status

    status = get_academy_status()
    progress = status["progress"]
    levels = progress.get("levels", {})

    print("=" * 60)
    print("ALNUA Academy Benchmark")
    print("=" * 60)
    print(f"Curriculum total     : {len(all_exercises())} exercices")
    print(f"Issues GitHub sync   : {status.get('github_issues_count', 0)}")
    print(f"Niveau courant       : N{progress.get('current_level', 1)}")
    print(f"Complétés            : {progress.get('completed_exercises', 0)}")
    print(f"Échoués              : {progress.get('failed_exercises', 0)}")
    print(f"Taux succès          : {progress.get('success_rate_pct', 0)}%")
    print()
    print("Par niveau :")
    for key in ("1", "2", "3", "4"):
        lv = levels.get(key, {})
        print(
            f"  N{key} {lv.get('name', '')}: "
            f"{lv.get('done', 0)}/{lv.get('total', 0)} done, "
            f"{lv.get('failed', 0)} failed, "
            f"{lv.get('in_progress', 0)} in progress"
        )

    print("\nGate NUAWAY :")
    gate = progress.get("gate_nuaway", {})
    for k, v in gate.items():
        mark = "OK" if v else "--"
        print(f"  [{mark}] {k}")

    if status.get("github_error"):
        print(f"\nGitHub sync error: {status['github_error']}")
    if not status.get("repo_configured"):
        print("\nAction: définir GITHUB_REPO_ACADEMY dans .env")

    print(f"\nManifest: {status.get('progress_file')}")
    print(json.dumps(progress, indent=2, ensure_ascii=False)[:1500])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
