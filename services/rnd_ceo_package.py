"""CEO package templates and dispatch matrix (phase 6) — façade.

Template structure from Emilie's validation dossier spec (2026-06-12):
1. Executive Summary
2. Bilan technique (branch-specific)
3. Réglementation / sécurité / RGPD
4. Industrialisation ou go-to-market
5. Business model multicouche (COGS, OPEX, revenus M6/M12)
6. Matrice des risques
7. R&D transverse IA (mutualisation)
8. Master summary portfolio
9. Matrice dispatch — qui fait quoi
"""

from __future__ import annotations

from services.rnd_ceo_package_build import build_ceo_package_json, build_ceo_package_md
from services.rnd_ceo_package_constants import (  # noqa: F401 — re-export
    BRANCH_BLOCKS,
    CEO_PACKAGE_OUTLINE,
    DISPATCH_POLES,
)
from services.rnd_ceo_package_dispatch import (  # noqa: F401 — re-export
    build_dispatch_matrix,
    build_portfolio_summary,
)
from services.rnd_ceo_package_helpers import resolve_branch  # noqa: F401 — re-export

__all__ = [
    "BRANCH_BLOCKS",
    "CEO_PACKAGE_OUTLINE",
    "DISPATCH_POLES",
    "build_ceo_package_json",
    "build_ceo_package_md",
    "build_dispatch_matrix",
    "build_portfolio_summary",
    "resolve_branch",
]
