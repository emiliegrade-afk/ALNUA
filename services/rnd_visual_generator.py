"""Generate illustrated assets for R&D dossiers (phase 4) — Pillow renders."""

from __future__ import annotations

import hashlib
import logging
import re
import textwrap
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from services.rnd_schemas import RndDossierOut

logger = logging.getLogger(__name__)

# ALNUA-inspired palette by branch
BRANCH_PALETTES: dict[str, dict[str, tuple[int, int, int]]] = {
    "app": {
        "bg": (18, 18, 22),
        "accent": (201, 149, 108),
        "text": (235, 232, 225),
        "muted": (140, 136, 128),
        "card": (32, 32, 38),
    },
    "gaming": {
        "bg": (14, 12, 28),
        "accent": (167, 139, 250),
        "text": (235, 232, 245),
        "muted": (130, 125, 150),
        "card": (28, 24, 48),
    },
    "robotics": {
        "bg": (12, 20, 24),
        "accent": (56, 189, 168),
        "text": (230, 240, 238),
        "muted": (120, 140, 135),
        "card": (20, 32, 36),
    },
    "other": {
        "bg": (18, 18, 22),
        "accent": (201, 149, 108),
        "text": (235, 232, 225),
        "muted": (140, 136, 128),
        "card": (32, 32, 38),
    },
}

ASSET_SPECS: list[dict[str, Any]] = [
    {
        "asset_type": "hero",
        "filename": "hero.png",
        "size": (1920, 1080),
        "section_key": "solution",
        "label": "Hero — couverture dossier",
    },
    {
        "asset_type": "social_teaser",
        "filename": "social_teaser.png",
        "size": (1080, 1080),
        "section_key": "solution",
        "label": "Teaser réseaux sociaux",
    },
    {
        "asset_type": "mockup",
        "filename": "mockup.png",
        "size": (1280, 800),
        "section_key": "mvp",
        "label": "Mockup produit",
    },
    {
        "asset_type": "diagram",
        "filename": "diagram.png",
        "size": (1200, 720),
        "section_key": "mvp",
        "label": "Schéma MVP",
    },
    {
        "asset_type": "moodboard",
        "filename": "moodboard.png",
        "size": (1400, 900),
        "section_key": "visual_identity",
        "label": "Moodboard identité",
    },
    {
        "asset_type": "chart",
        "filename": "finance_chart.png",
        "size": (1200, 680),
        "section_key": "business_case",
        "label": "Synthèse finance",
        "requires_finance": True,
    },
]


def _palette(dossier: RndDossierOut) -> dict[str, tuple[int, int, int]]:
    branch = (dossier.branch or "other").lower()
    if branch not in BRANCH_PALETTES:
        branch = "other"
    return BRANCH_PALETTES[branch]


def _section_excerpt(dossier: RndDossierOut, key: str, max_len: int = 220) -> str:
    for sec in dossier.sections:
        if sec.section_key == key:
            text = (sec.content_md or "").strip()
            if len(text) > 20 and not text.startswith("_"):
                clean = re.sub(r"[#*_>`]", "", text.split("\n\n")[0])
                return clean[:max_len].strip()
    return dossier.tagline or dossier.title


def _load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_wrapped(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    font: ImageFont.ImageFont,
    fill: tuple[int, int, int],
    max_width: int,
    line_spacing: int = 8,
) -> int:
    """Draw wrapped text; return bottom y."""
    x, y = xy
    lines: list[str] = []
    for paragraph in text.split("\n"):
        lines.extend(textwrap.wrap(paragraph, width=max(20, max_width // 12)) or [""])
    for line in lines[:12]:
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_spacing if hasattr(font, "size") else 18
    return y


def _render_hero(dossier: RndDossierOut, pal: dict[str, tuple[int, int, int]], size: tuple[int, int]) -> Image.Image:
    img = Image.new("RGB", size, pal["bg"])
    draw = ImageDraw.Draw(img)
    w, h = size
    draw.rectangle([(0, 0), (w, 6)], fill=pal["accent"])
    draw.rectangle([(40, 80), (w - 40, h - 80)], outline=pal["accent"], width=2)
    title_font = _load_font(72, bold=True)
    sub_font = _load_font(32)
    label_font = _load_font(22)
    draw.text((80, 120), dossier.title[:60], font=title_font, fill=pal["text"])
    tag = dossier.tagline or _section_excerpt(dossier, "solution", 120)
    _draw_wrapped(draw, tag, (80, 220), sub_font, pal["muted"], w - 160)
    draw.text((80, h - 120), f"ALNUA R&D · {dossier.domain.upper()}", font=label_font, fill=pal["accent"])
    draw.text((80, h - 80), dossier.slug, font=label_font, fill=pal["muted"])
    return img


def _render_social_teaser(
    dossier: RndDossierOut, pal: dict[str, tuple[int, int, int]], size: tuple[int, int]
) -> Image.Image:
    img = Image.new("RGB", size, pal["bg"])
    draw = ImageDraw.Draw(img)
    s = size[0]
    draw.ellipse([(s // 2 - 200, s // 2 - 200), (s // 2 + 200, s // 2 + 200)], outline=pal["accent"], width=3)
    title_font = _load_font(48, bold=True)
    body_font = _load_font(28)
    draw.text((80, 80), dossier.title[:40], font=title_font, fill=pal["text"])
    problem = _section_excerpt(dossier, "problem", 100)
    _draw_wrapped(draw, problem, (80, 160), body_font, pal["muted"], s - 160)
    draw.text((80, s - 100), "Bientôt · ALNUA", font=body_font, fill=pal["accent"])
    return img


def _render_mockup(
    dossier: RndDossierOut, pal: dict[str, tuple[int, int, int]], size: tuple[int, int]
) -> Image.Image:
    img = Image.new("RGB", size, pal["bg"])
    draw = ImageDraw.Draw(img)
    w, h = size
    # Phone frame
    fx, fy = w // 4, 60
    fw, fh = w // 2, h - 120
    draw.rounded_rectangle([(fx, fy), (fx + fw, fy + fh)], radius=24, fill=pal["card"], outline=pal["accent"], width=2)
    draw.rectangle([(fx + 20, fy + 50), (fx + fw - 20, fy + 120)], fill=pal["accent"])
    title_font = _load_font(28, bold=True)
    body_font = _load_font(20)
    draw.text((fx + 30, fy + 65), dossier.title[:25], font=title_font, fill=pal["bg"])
    mvp = _section_excerpt(dossier, "mvp", 180)
    _draw_wrapped(draw, mvp, (fx + 30, fy + 150), body_font, pal["text"], fw - 60)
    draw.text((40, h - 50), "Mockup MVP — wireframe dossier R&D", font=body_font, fill=pal["muted"])
    return img


def _render_diagram(
    dossier: RndDossierOut, pal: dict[str, tuple[int, int, int]], size: tuple[int, int]
) -> Image.Image:
    img = Image.new("RGB", size, pal["bg"])
    draw = ImageDraw.Draw(img)
    w, h = size
    boxes = [
        ("Problème", _section_excerpt(dossier, "problem", 60)),
        ("Solution", _section_excerpt(dossier, "solution", 60)),
        ("MVP", _section_excerpt(dossier, "mvp", 60)),
    ]
    bw = (w - 160) // 3
    y = 120
    font = _load_font(22, bold=True)
    small = _load_font(18)
    for i, (label, body) in enumerate(boxes):
        x = 40 + i * (bw + 40)
        draw.rounded_rectangle([(x, y), (x + bw, y + 400)], radius=12, fill=pal["card"], outline=pal["accent"])
        draw.text((x + 16, y + 16), label, font=font, fill=pal["accent"])
        _draw_wrapped(draw, body, (x + 16, y + 56), small, pal["text"], bw - 32)
        if i < 2:
            ax = x + bw + 8
            draw.line([(ax, y + 200), (ax + 24, y + 200)], fill=pal["accent"], width=2)
            draw.polygon([(ax + 24, y + 195), (ax + 32, y + 200), (ax + 24, y + 205)], fill=pal["accent"])
    draw.text((40, h - 50), "Pipeline produit — extrait sections dossier", font=small, fill=pal["muted"])
    return img


def _render_moodboard(
    dossier: RndDossierOut, pal: dict[str, tuple[int, int, int]], size: tuple[int, int]
) -> Image.Image:
    img = Image.new("RGB", size, pal["bg"])
    draw = ImageDraw.Draw(img)
    w, h = size
    swatches = [pal["accent"], pal["card"], pal["text"], pal["muted"], (80, 80, 90), (60, 60, 68)]
    for i, color in enumerate(swatches):
        x = 40 + (i % 3) * 200
        y = 80 + (i // 3) * 200
        draw.rounded_rectangle([(x, y), (x + 180, y + 160)], radius=8, fill=color)
    font = _load_font(24, bold=True)
    small = _load_font(18)
    draw.text((40, 520), "Identité visuelle", font=font, fill=pal["text"])
    visual = _section_excerpt(dossier, "visual_identity", 300)
    _draw_wrapped(draw, visual, (40, 560), small, pal["muted"], w - 80)
    return img


def _render_finance_chart(
    dossier: RndDossierOut, pal: dict[str, tuple[int, int, int]], size: tuple[int, int]
) -> Image.Image:
    img = Image.new("RGB", size, pal["bg"])
    draw = ImageDraw.Draw(img)
    w, h = size
    fj = dossier.finance_json or {}
    rev = fj.get("revenue_hypothesis") or {}
    m3 = float(rev.get("m3_monthly_run_rate_eur") or 0)
    m6 = float(rev.get("m6_monthly_run_rate_eur") or 0)
    m12 = float(rev.get("m12_monthly_run_rate_eur") or 0)
    values = [("M3", m3), ("M6", m6), ("M12", m12)]
    max_v = max(v for _, v in values) or 1
    bar_w = 120
    base_y = h - 100
    font = _load_font(22, bold=True)
    small = _load_font(18)
    draw.text((40, 40), "Run-rate revenus (hypothèses)", font=font, fill=pal["text"])
    draw.text(
        (40, 80),
        f"CAPEX {fj.get('capex_eur', '—')} € · Verdict {fj.get('verdict_finance', '—')}",
        font=small,
        fill=pal["muted"],
    )
    for i, (label, val) in enumerate(values):
        x = 120 + i * 280
        bar_h = int((val / max_v) * (h - 220))
        draw.rectangle([(x, base_y - bar_h), (x + bar_w, base_y)], fill=pal["accent"])
        draw.text((x, base_y + 10), label, font=small, fill=pal["text"])
        draw.text((x, base_y - bar_h - 28), f"{int(val)} €", font=small, fill=pal["accent"])
    return img


RENDERERS = {
    "hero": _render_hero,
    "social_teaser": _render_social_teaser,
    "mockup": _render_mockup,
    "diagram": _render_diagram,
    "moodboard": _render_moodboard,
    "chart": _render_finance_chart,
}


def build_image_prompt(dossier: RndDossierOut, spec: dict[str, Any]) -> str:
    key = spec.get("section_key", "solution")
    excerpt = _section_excerpt(dossier, key, 150)
    return (
        f"{spec['label']} for {dossier.title} ({dossier.domain}): {excerpt}. "
        f"Style ALNUA, dark premium, accent copper."
    )


def generate_dossier_assets(
    dossier: RndDossierOut,
    *,
    output_dir: Path,
    force: bool = False,
) -> list[dict[str, Any]]:
    """Render PNG assets to output_dir; return metadata rows for DB insert."""
    output_dir.mkdir(parents=True, exist_ok=True)
    pal = _palette(dossier)
    created: list[dict[str, Any]] = []

    for spec in ASSET_SPECS:
        if spec.get("requires_finance") and not dossier.finance_json:
            continue
        path = output_dir / spec["filename"]
        if path.exists() and not force:
            created.append(_asset_row(dossier, spec, path, skipped=True))
            continue

        renderer = RENDERERS.get(spec["asset_type"])
        if not renderer:
            continue
        try:
            image = renderer(dossier, pal, spec["size"])
            image.save(path, format="PNG", optimize=True)
            created.append(_asset_row(dossier, spec, path, skipped=False))
        except Exception as exc:
            logger.warning("asset render %s failed: %s", spec["asset_type"], exc)

    return created


def _asset_row(
    dossier: RndDossierOut,
    spec: dict[str, Any],
    path: Path,
    *,
    skipped: bool,
) -> dict[str, Any]:
    w, h = spec["size"]
    rel = f"data/rnd_dossiers/{dossier.slug}/assets/{spec['filename']}"
    return {
        "dossier_id": dossier.id,
        "section_key": spec.get("section_key"),
        "asset_type": spec["asset_type"],
        "file_path": rel.replace("\\", "/"),
        "public_url": None,
        "image_prompt": build_image_prompt(dossier, spec),
        "generation_model": "pillow_v1",
        "width": w,
        "height": h,
        "metadata": {"label": spec["label"], "skipped_existing": skipped},
    }
