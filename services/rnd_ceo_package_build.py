"""CEO package markdown and JSON assembly."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from services.rnd_ceo_package_blocks import build_block_content
from services.rnd_ceo_package_constants import BRANCH_BLOCKS
from services.rnd_ceo_package_dispatch import build_dispatch_matrix, build_portfolio_summary
from services.rnd_ceo_package_helpers import (
    extract_go_recommendation,
    finance_summary,
    resolve_branch,
    section_map,
)
from services.rnd_schemas import RndDossierOut


def build_ceo_package_md(
    dossier: RndDossierOut,
    *,
    committee_report_md: str | None = None,
    committee_transcript_md: str | None = None,
    portfolio_rows: list[dict[str, Any]] | None = None,
) -> str:
    branch = resolve_branch(dossier)
    sections = section_map(dossier)
    blocks = BRANCH_BLOCKS.get(branch, BRANCH_BLOCKS["other"])
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    lines = [
        f"# Dossier CEO — {dossier.title}",
        f"*{dossier.tagline or dossier.domain} · {branch.upper()} · généré {now}*",
        "",
        "> Dossier de validation CEO — pourquoi du comment, chiffres, risques, dispatch.",
        "",
        "---",
        "",
    ]

    if committee_report_md and len(committee_report_md.strip()) > 40:
        lines.extend(
            [
                "## Compte-rendu comité R&D",
                "",
                committee_report_md.strip(),
                "",
                "---",
                "",
            ]
        )

    if committee_transcript_md and len(committee_transcript_md.strip()) > 80:
        lines.extend(
            [
                "## Synthèse des échanges — réunion comité",
                "",
                "_Décisions, chiffres et demandes discutés en salle (source : transcript)._",
                "",
                committee_transcript_md.strip()[:28000],
                "",
                "---",
                "",
            ]
        )

    for block in blocks:
        content = build_block_content(block["key"], dossier, sections)
        lines.extend([f"## {block['title']}", "", content, "", "---", ""])

    lines.extend(
        [
            "## 7. R&D transverse — socle IA mutualisé",
            "",
            build_block_content("rd_transverse", dossier, sections),
            "",
            "---",
            "",
            "## 8. Master Summary — roadmap portfolio",
            "",
            build_portfolio_summary(dossier, portfolio_rows=portfolio_rows),
            "",
            "---",
            "",
            "## 9. Matrice dispatch — qui fait quoi, quoi envoyer à qui",
            "",
            "| Pôle | Agent | Livrables à envoyer | Priorité |",
            "|------|-------|---------------------|----------|",
        ]
    )

    for row in build_dispatch_matrix(dossier):
        deliverables = "; ".join(row["deliverables"][:2])
        lines.append(
            f"| {row['pole']} | {row['agent_id']} | {deliverables} | {row['priority']} |"
        )

    lines.extend(
        [
            "",
            "---",
            "",
            "*Dossier CEO ALNUA — validation Emilie requise avant dispatch COO.*",
        ]
    )
    return "\n".join(lines)


def build_ceo_package_json(
    dossier: RndDossierOut,
    *,
    committee_report_md: str | None = None,
    committee_transcript_md: str | None = None,
    markdown: str | None = None,
    portfolio_rows: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    branch = resolve_branch(dossier)
    sections = section_map(dossier)
    blocks = BRANCH_BLOCKS.get(branch, BRANCH_BLOCKS["other"])
    block_contents = {
        b["key"]: {"title": b["title"], "content_md": build_block_content(b["key"], dossier, sections)}
        for b in blocks
    }
    block_contents["rd_transverse"] = {
        "title": "7. R&D transverse — socle IA mutualisé",
        "content_md": build_block_content("rd_transverse", dossier, sections),
    }
    md = markdown or build_ceo_package_md(
        dossier,
        committee_report_md=committee_report_md,
        committee_transcript_md=committee_transcript_md,
        portfolio_rows=portfolio_rows,
    )
    return {
        "version": 2,
        "branch": branch,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dossier_id": dossier.id,
        "dossier_slug": dossier.slug,
        "title": dossier.title,
        "markdown": md,
        "blocks": block_contents,
        "finance_summary": finance_summary(dossier),
        "dispatch_matrix": build_dispatch_matrix(dossier),
        "portfolio_summary": build_portfolio_summary(dossier, portfolio_rows=portfolio_rows),
        "portfolio_rows": portfolio_rows or [],
        "committee_report_md": committee_report_md,
        "committee_transcript_md": committee_transcript_md,
        "recommendation": extract_go_recommendation(sections.get("decision", "")),
    }
