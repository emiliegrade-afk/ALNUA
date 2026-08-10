"""CEO package dispatch matrix and portfolio summary builders."""

from __future__ import annotations

from typing import Any

from services.rnd_ceo_package_constants import DISPATCH_POLES
from services.rnd_ceo_package_helpers import resolve_branch
from services.rnd_schemas import RndDossierOut


def build_dispatch_matrix(dossier: RndDossierOut) -> list[dict[str, Any]]:
    branch = resolve_branch(dossier)
    base = DISPATCH_POLES.get(branch, DISPATCH_POLES["other"])
    matrix: list[dict[str, Any]] = []
    for row in base:
        matrix.append(
            {
                **row,
                "roadmap_title": f"[{dossier.title}] {row['deliverables'][0]}",
                "description": (
                    f"Dispatch post-validation CEO — {dossier.title}.\n"
                    f"**À envoyer à :** {row['pole']} ({row['agent_id']}).\n"
                    f"**Livrables :** {', '.join(row['deliverables'])}."
                ),
            }
        )
    matrix.append(
        {
            "pole": "COO (orchestration)",
            "agent_id": "coo_agent",
            "deliverables": [
                "Plan d'exécution multi-pôles",
                "Suivi roadmap & arbitrages",
            ],
            "priority": "high",
            "phase": "orchestration",
            "roadmap_title": f"[{dossier.title}] Orchestration COO",
            "description": (
                f"Le COO prend le relais **après** validation CEO sur {dossier.title}. "
                "Coordonne les pôles — pas de présence en comité R&D."
            ),
        }
    )
    return matrix


def build_portfolio_summary(
    dossier: RndDossierOut,
    *,
    portfolio_rows: list[dict[str, Any]] | None = None,
) -> str:
    branch = resolve_branch(dossier)
    branch_label = {
        "app": "Software / App",
        "robotics": "Robotique / Hardware full stack",
        "gaming": "Logiciel lourd / Plateforme 3D",
        "hub": "Hub ALNUA — infra interne entreprise",
        "other": "Transverse",
    }.get(branch, branch)
    lines = [
        f"**Typologie dossier :** {branch_label}",
        f"**Statut :** {dossier.status} · **CEO :** {dossier.ceo_status}",
        f"**Sections validées :** {dossier.sections_validated_count}/{dossier.sections_total_count}",
        "",
        "Ordre de priorisation suggéré (portfolio ALNUA) :",
        "- **Court terme :** apps SaaS — cash-flow rapide, test marché.",
        "- **Moyen terme :** modules IA & contenu mutualisés.",
        "- **Long terme :** hardware / robotique — inertie fabrication.",
    ]

    if portfolio_rows:
        lines.extend(["", "### Roadmap portfolio ALNUA", ""])
        lines.append("| Projet | Branche | Statut | CEO | Validé |")
        lines.append("|--------|---------|--------|-----|--------|")
        for row in portfolio_rows[:15]:
            title = str(row.get("title", "—"))[:36]
            dom = row.get("domain") or row.get("branch") or "—"
            st = row.get("status", "—")
            ceo = row.get("ceo_status", "—")
            val = f"{row.get('sections_validated_count', 0)}/{row.get('sections_total_count', 0)}"
            marker = "**→** " if str(row.get("id")) == str(dossier.id) else ""
            lines.append(f"| {marker}{title} | {dom} | {st} | {ceo} | {val} |")

    return "\n".join(lines)
