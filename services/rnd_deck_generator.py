"""Generate investor-style HTML deck + PDF from R&D dossier sections."""

from __future__ import annotations

import html
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from services.rnd_finance_estimate import finance_json_to_markdown
from services.rnd_schemas import RndDossierOut

logger = logging.getLogger(__name__)

_PLACEHOLDER_PREFIXES = (
    "_À compléter",
    "_Business case à générer",
    "_Risques à identifier",
)


def _is_placeholder(content: str) -> bool:
    t = (content or "").strip()
    if not t or len(t) < 20:
        return True
    return any(t.startswith(p) for p in _PLACEHOLDER_PREFIXES)


def md_to_html(md: str) -> str:
    """Minimal markdown → HTML (no external deps)."""
    if not md.strip():
        return ""

    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    in_ul = False
    in_ol = False

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def inline(text: str) -> str:
        text = html.escape(text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
        return text

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            close_lists()
            continue

        hm = re.match(r"^(#{1,4})\s+(.+)$", line)
        if hm:
            close_lists()
            level = len(hm.group(1))
            out.append(f"<h{level}>{inline(hm.group(2))}</h{level}>")
            continue

        if re.match(r"^[-*]\s+", line):
            if not in_ul:
                close_lists()
                in_ul = True
                out.append("<ul>")
            out.append(f"<li>{inline(re.sub(r'^[-*]\s+', '', line))}</li>")
            continue

        if re.match(r"^\d+\.\s+", line):
            if not in_ol:
                close_lists()
                in_ol = True
                out.append("<ol>")
            out.append(f"<li>{inline(re.sub(r'^\d+\.\s+', '', line))}</li>")
            continue

        close_lists()
        out.append(f"<p>{inline(line)}</p>")

    close_lists()
    return "\n".join(out)


def _deck_css() -> str:
    return """
    @page { size: A4 landscape; margin: 0; }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: 'Segoe UI', system-ui, sans-serif;
      background: #0E1014;
      color: #F5F2EA;
    }
    .slide {
      min-height: 100vh;
      page-break-after: always;
      padding: 48px 56px;
      display: flex;
      flex-direction: column;
      justify-content: center;
      background: linear-gradient(135deg, #0E1014 0%, #151820 100%);
      border-bottom: 1px solid rgba(192, 138, 98, 0.15);
    }
    .slide:last-child { page-break-after: auto; }
    .slide-title {
      background: linear-gradient(90deg, rgba(192,138,98,0.12), transparent);
    }
    h1 {
      font-size: 2.4rem;
      font-weight: 600;
      color: #F5F2EA;
      margin: 0 0 12px;
      line-height: 1.15;
    }
    h2 {
      font-size: 1.5rem;
      font-weight: 600;
      color: #C08A62;
      margin: 0 0 24px;
      letter-spacing: 0.02em;
    }
    .tagline {
      font-size: 1.15rem;
      color: rgba(245, 242, 234, 0.75);
      max-width: 720px;
      line-height: 1.5;
    }
    .meta {
      margin-top: 32px;
      font-size: 0.85rem;
      color: rgba(167, 173, 181, 0.8);
    }
    .meta span {
      display: inline-block;
      margin-right: 16px;
      padding: 4px 10px;
      border: 1px solid rgba(192, 138, 98, 0.25);
      border-radius: 999px;
    }
    .content {
      font-size: 0.95rem;
      line-height: 1.55;
      color: rgba(245, 242, 234, 0.88);
      max-width: 900px;
    }
    .content p { margin: 0 0 12px; }
    .content ul, .content ol { margin: 0 0 12px; padding-left: 1.4em; }
    .content li { margin-bottom: 6px; }
    .content strong { color: #C08A62; }
    .content h3, .content h4 { color: #F5F2EA; margin: 16px 0 8px; font-size: 1rem; }
    .footer-brand {
      margin-top: auto;
      padding-top: 24px;
      font-size: 0.75rem;
      color: rgba(167, 173, 181, 0.5);
      letter-spacing: 0.08em;
      text-transform: uppercase;
    }
    """


def build_deck_html(dossier: RndDossierOut) -> str:
    """Build a slide-style HTML deck from dossier sections."""
    sections = [
        s for s in dossier.sections
        if not _is_placeholder(s.content_md)
    ]

    slides: list[str] = []
    tagline = html.escape(dossier.tagline or "")
    domain = html.escape(dossier.domain or "")
    branch = html.escape(dossier.branch or "other")
    title = html.escape(dossier.title)

    slides.append(
        f"""
        <section class="slide slide-title">
          <h1>{title}</h1>
          {f'<p class="tagline">{tagline}</p>' if tagline else ''}
          <div class="meta">
            <span>{domain}</span>
            <span>{branch}</span>
            <span>ALNUA R&D</span>
          </div>
          <p class="footer-brand">Dossier {html.escape(dossier.slug)} · {datetime.utcnow().strftime('%Y-%m-%d')}</p>
        </section>
        """
    )

    for sec in sections:
        body = md_to_html(sec.content_md)
        if sec.section_key == "business_case" and dossier.finance_json:
            finance_md = finance_json_to_markdown(dossier.finance_json)
            body = md_to_html(finance_md) + body

        slides.append(
            f"""
            <section class="slide">
              <h2>{html.escape(sec.title)}</h2>
              <div class="content">{body}</div>
              <p class="footer-brand">ALNUA · {html.escape(dossier.slug)}</p>
            </section>
            """
        )

    if not sections:
        slides.append(
            """
            <section class="slide">
              <h2>Contenu à compléter</h2>
              <div class="content">
                <p>Enrichissez le dossier (agents ou comité) avant de regénérer le deck.</p>
              </div>
            </section>
            """
        )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8"/>
  <title>{title} — Deck R&D ALNUA</title>
  <style>{_deck_css()}</style>
</head>
<body>
{"".join(slides)}
</body>
</html>
"""


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
            _html_to_pdf(html_path, pdf_path)
        except Exception as exc:
            logger.warning("rnd_deck: PDF export failed for %s: %s", slug, exc)
            pdf_error = str(exc)
            pdf_path = None

    repo_root = (root or RND_DOSSIERS_ROOT).parent.parent
    html_rel = _relative_path(html_path, repo_root)
    pdf_rel = _relative_path(pdf_path, repo_root) if pdf_path else None

    return {
        "html_path": str(html_path.resolve()),
        "pdf_path": str(pdf_path.resolve()) if pdf_path else None,
        "html_rel": html_rel,
        "pdf_rel": pdf_rel,
        "slide_count": max(1, len([s for s in dossier.sections if not _is_placeholder(s.content_md)])),
        "pdf_error": pdf_error,
    }


def _relative_path(path: Path | None, repo_root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    """HTML → PDF: Edge/Chrome on Windows (no install), Playwright elsewhere."""
    import sys

    errors: list[str] = []

    # Windows: Edge is preinstalled — no pip/playwright install needed
    if sys.platform == "win32":
        try:
            _html_to_pdf_headless_browser(html_path, pdf_path)
            return
        except Exception as exc:
            errors.append(f"Edge/Chrome: {exc}")

    try:
        _html_to_pdf_playwright(html_path, pdf_path)
        return
    except Exception as exc:
        errors.append(f"Playwright: {exc}")

    if sys.platform != "win32":
        try:
            _html_to_pdf_headless_browser(html_path, pdf_path)
            return
        except Exception as exc:
            errors.append(f"Navigateur headless: {exc}")

    raise RuntimeError(
        "Export PDF impossible. "
        + " ; ".join(errors)
        + " — Ouvre le HTML et Ctrl+P → Enregistrer en PDF."
    )


def _html_to_pdf_playwright(html_path: Path, pdf_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    file_url = html_path.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(file_url, wait_until="networkidle")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                landscape=True,
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
        finally:
            browser.close()


def _html_to_pdf_headless_browser(html_path: Path, pdf_path: Path) -> None:
    """Windows fallback: Edge or Chrome --headless --print-to-pdf."""
    import os
    import subprocess
    import sys

    if sys.platform != "win32":
        raise RuntimeError("fallback Windows uniquement")

    candidates = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
    ]
    exe = next((p for p in candidates if p and Path(p).is_file()), None)
    if not exe:
        raise RuntimeError("Edge/Chrome introuvable")

    file_url = html_path.resolve().as_uri()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        pdf_path.unlink()

    result = subprocess.run(
        [
            exe,
            "--headless=new",
            "--disable-gpu",
            f"--print-to-pdf={pdf_path.resolve()}",
            file_url,
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0 or not pdf_path.is_file():
        detail = (result.stderr or result.stdout or "").strip()[:200]
        raise RuntimeError(detail or f"code {result.returncode}")
