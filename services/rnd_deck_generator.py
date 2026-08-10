"""Generate investor-style HTML deck + PDF from R&D dossier sections (facade)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from services.rnd_deck_html import build_deck_html  # noqa: F401 — re-export
from services.rnd_deck_markdown import is_placeholder, md_to_html  # noqa: F401 — re-export
from services.rnd_deck_pdf import html_to_pdf, relative_path
from services.rnd_schemas import RndDossierOut

logger = logging.getLogger(__name__)

_is_placeholder = is_placeholder


def write_deck_files(
    dossier: RndDossierOut,
    *,
    root: Path | None = None,
    export_pdf: bool = True,
) -> dict[str, Any]:
    """
    Write deck HTML (and PDF if Playwright available) under data/rnd_dossiers/{slug}/deck/.
    Returns paths relative to repo root when possible.
    """
    from services.rnd_repository import RND_DOSSIERS_ROOT

    slug = dossier.slug
    deck_dir = (root or RND_DOSSIERS_ROOT) / slug / "deck"
    deck_dir.mkdir(parents=True, exist_ok=True)

    html_content = build_deck_html(dossier)
    html_path = deck_dir / "index.html"
    html_path.write_text(html_content, encoding="utf-8")

    pdf_path: Path | None = None
    pdf_error: str | None = None

    if export_pdf:
        pdf_path = deck_dir / "deck.pdf"
        try:
            html_to_pdf(html_path, pdf_path)
        except Exception as exc:
            logger.warning("rnd_deck: PDF export failed for %s: %s", slug, exc)
            pdf_error = str(exc)
            pdf_path = None

    repo_root = (root or RND_DOSSIERS_ROOT).parent.parent
    html_rel = relative_path(html_path, repo_root)
    pdf_rel = relative_path(pdf_path, repo_root) if pdf_path else None

    return {
        "html_path": str(html_path.resolve()),
        "pdf_path": str(pdf_path.resolve()) if pdf_path else None,
        "html_rel": html_rel,
        "pdf_rel": pdf_rel,
        "slide_count": max(
            1, len([s for s in dossier.sections if not is_placeholder(s.content_md)])
        ),
        "pdf_error": pdf_error,
    }


__all__ = [
    "_is_placeholder",
    "build_deck_html",
    "md_to_html",
    "write_deck_files",
]
