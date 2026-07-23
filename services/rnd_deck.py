"""Orchestrate deck generation for R&D dossiers."""

from __future__ import annotations

import logging
from typing import Any

from services.rnd_deck_generator import write_deck_files
from services.rnd_repository import get_rnd_repository

logger = logging.getLogger(__name__)


def generate_dossier_deck(
    dossier_id: str,
    *,
    export_pdf: bool = True,
    actor: str = "rnd_deck_generator",
) -> dict[str, Any]:
    repo = get_rnd_repository()
    dossier = repo.get_dossier(dossier_id)
    if not dossier:
        raise ValueError(f"Dossier introuvable : {dossier_id}")

    result = write_deck_files(dossier, export_pdf=export_pdf)

    html_store = result.get("html_rel") or result["html_path"]
    pdf_store = result.get("pdf_rel") or result.get("pdf_path")

    one_pager = _build_one_pager_md(dossier)
    updated = repo.set_deck_paths(
        dossier.id,
        html_path=html_store,
        pdf_path=pdf_store,
        one_pager_md=one_pager,
    )

    repo.log_event(
        dossier.id,
        "deck_generated",
        actor,
        {
            "slide_count": result.get("slide_count", 0),
            "pdf_error": result.get("pdf_error"),
        },
    )

    return {
        "dossier_id": dossier.id,
        "html_path": html_store,
        "pdf_path": pdf_store,
        "slide_count": result.get("slide_count", 0),
        "pdf_error": result.get("pdf_error"),
        "one_pager_md": one_pager[:500] if one_pager else None,
        "dossier": updated.model_dump() if updated else None,
        "message": "Deck HTML généré"
        + (" + PDF" if pdf_store else " (PDF indisponible — voir pdf_error)"),
    }


def _build_one_pager_md(dossier) -> str:
    """Executive one-pager markdown for CEO handoff preview."""
    lines = [
        f"# {dossier.title}",
        "",
        dossier.tagline or "",
        "",
        f"**Domaine :** {dossier.domain} · **Branche :** {dossier.branch or 'other'}",
        "",
    ]
    for sec in dossier.sections:
        content = (sec.content_md or "").strip()
        if len(content) < 30 or content.startswith("_"):
            continue
        excerpt = content.split("\n\n")[0][:400]
        lines.extend([f"## {sec.title}", "", excerpt, ""])
    if dossier.finance_json:
        verdict = dossier.finance_json.get("verdict_finance", "")
        capex = dossier.finance_json.get("capex_eur", 0)
        lines.extend([
            "## Finance (synthèse)",
            "",
            f"- CAPEX : {capex} €",
            f"- Verdict : {verdict}",
            "",
        ])
    return "\n".join(lines).strip()
