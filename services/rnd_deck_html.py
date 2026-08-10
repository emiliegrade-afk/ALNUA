"""R&D deck — slide HTML assembly."""

from __future__ import annotations

import html
from datetime import datetime

from services.rnd_deck_markdown import is_placeholder, md_to_html
from services.rnd_finance_estimate import finance_json_to_markdown
from services.rnd_schemas import RndDossierOut


def deck_css() -> str:
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
    sections = [s for s in dossier.sections if not is_placeholder(s.content_md)]

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
  <style>{deck_css()}</style>
</head>
<body>
{"".join(slides)}
</body>
</html>
"""
