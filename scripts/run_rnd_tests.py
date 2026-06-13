"""Run all R&D dossier test scripts (phase 8 orchestrator)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = [
    "test_rnd_dossier.py",
    "test_rnd_committee.py",
    "test_rnd_visual.py",
    "test_rnd_social.py",
    "test_rnd_ceo.py",
    "test_rnd_product.py",
    "test_rnd_pipeline.py",
    "test_rnd_e2e.py",
]


def main() -> int:
    failed: list[str] = []
    print("=== R&D test suite (phase 8) ===\n")
    for name in SCRIPTS:
        path = ROOT / "scripts" / name
        if not path.is_file():
            print(f"SKIP {name} (missing)")
            continue
        print(f"--- {name} ---")
        result = subprocess.run(
            [sys.executable, str(path)],
            cwd=str(ROOT),
            env={**os.environ, "PYTHONUTF8": "1", "RND_DOSSIER_USE_LLM": "false"},
        )
        if result.returncode != 0:
            failed.append(name)
        print()
    if failed:
        print(f"FAILED: {', '.join(failed)}")
        return 1
    print("All R&D tests passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
