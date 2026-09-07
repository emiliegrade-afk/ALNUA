"""
main.py — Spark (assistante desktop ALNUA)
Persona chat = Nadia Faure. UI = maquette WebView2.

Lance : python main.py  |  Spark.bat
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
try:
    _log = Path(__file__).resolve().parent.parent / "data" / "spark.log"
    _log.parent.mkdir(parents=True, exist_ok=True)
    _fh = logging.FileHandler(_log, encoding="utf-8")
    _fh.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)s] %(name)s — %(message)s")
    )
    logging.getLogger().addHandler(_fh)
except Exception:
    pass

logger = logging.getLogger("spark.main")


def main() -> None:
    from spark_shell import run

    logger.info("Spark demarre — persona Nadia")
    raise SystemExit(run())


if __name__ == "__main__":
    main()
