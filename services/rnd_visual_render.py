"""Pillow renderers for R&D dossier visual assets."""

from __future__ import annotations

import re
import textwrap
from typing import Callable

from PIL import Image, ImageDraw, ImageFont

from services.rnd_schemas import RndDossierOut
from services.rnd_visual_constants import BRANCH_PALETTES

Renderer = Callable[
    [RndDossierOut, dict[str, tuple[int, int, int]], tuple[int, int]],
    Image.Image,
]


def palette(dossier: RndDossierOut) -> dict[str, tuple[int, int, int]]:
    branch = (dossier.branch or "other").lower()
    if branch not in BRANCH_PALETTES:
        branch = "other"
    return BRANCH_PALETTES[branch]


def section_excerpt(dossier: RndDossierOut, key: str, max_len: int = 220) -> str:
    for sec in dossier.sections:
        if sec.section_key == key:
            text = (sec.content_md or "").strip()
            if len(text) > 20 and not text.startswith("_"):
                clean = re.sub(r"[#*_>`]", "", text.split("\n\n")[0])
                return clean[:max_len].strip()
    return dossier.tagline or dossier.title


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw_wrapped(
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


def render_hero(
    dossier: RndDossierOut, pal: dict[str, tuple[int, int, int]], size: tuple[int, int]
) -> Image.Image:
    img = Image.new("RGB", size, pal["bg"])
    draw = ImageDraw.Draw(img)
    w, h = size
    draw.rectangle([(0, 0), (w, 6)], fill=pal["accent"])
    draw.rectangle([(40, 80), (w - 40, h - 80)], outline=pal["accent"], width=2)
    title_font = load_font(72, bold=True)
    sub_font = load_font(32)
    label_font = load_font(22)
    draw.text((80, 120), dossier.title[:60], font=title_font, fill=pal["text"])
    tag = dossier.tagline or section_excerpt(dossier, "solution", 120)
    draw_wrapped(draw, tag, (80, 220), sub_font, pal["muted"], w - 160)
    draw.text((80, h - 120), f"ALNUA R&D · {dossier.domain.upper()}", font=label_font, fill=pal["accent"])
    draw.text((80, h - 80), dossier.slug, font=label_font, fill=pal["muted"])
    return img


def render_social_teaser(
    dossier: RndDossierOut, pal: dict[str, tuple[int, int, int]], size: tuple[int, int]
) -> Image.Image:
    img = Image.new("RGB", size, pal["bg"])
    draw = ImageDraw.Draw(img)
    s = size[0]
    draw.ellipse(
        [(s // 2 - 200, s // 2 - 200), (s // 2 + 200, s // 2 + 200)],
        outline=pal["accent"],
        width=3,
    )
    title_font = load_font(48, bold=True)
    body_font = load_font(28)
    draw.text((80, 80), dossier.title[:40], font=title_font, fill=pal["text"])
    problem = section_excerpt(dossier, "problem", 100)
    draw_wrapped(draw, problem, (80, 160), body_font, pal["muted"], s - 160)
    draw.text((80, s - 100), "Bientôt · ALNUA", font=body_font, fill=pal["accent"])
    return img


def render_mockup(
    dossier: RndDossierOut, pal: dict[str, tuple[int, int, int]], size: tuple[int, int]
) -> Image.Image:
    img = Image.new("RGB", size, pal["bg"])
    draw = ImageDraw.Draw(img)
    w, h = size
    fx, fy = w // 4, 60
    fw, fh = w // 2, h - 120
    draw.rounded_rectangle(
        [(fx, fy), (fx + fw, fy + fh)], radius=24, fill=pal["card"], outline=pal["accent"], width=2
    )
    draw.rectangle([(fx + 20, fy + 50), (fx + fw - 20, fy + 120)], fill=pal["accent"])
    title_font = load_font(28, bold=True)
    body_font = load_font(20)
    draw.text((fx + 30, fy + 65), dossier.title[:25], font=title_font, fill=pal["bg"])
    mvp = section_excerpt(dossier, "mvp", 180)
    draw_wrapped(draw, mvp, (fx + 30, fy + 150), body_font, pal["text"], fw - 60)
    draw.text((40, h - 50), "Mockup MVP — wireframe dossier R&D", font=body_font, fill=pal["muted"])
    return img


def render_diagram(
    dossier: RndDossierOut, pal: dict[str, tuple[int, int, int]], size: tuple[int, int]
) -> Image.Image:
    img = Image.new("RGB", size, pal["bg"])
    draw = ImageDraw.Draw(img)
    w, h = size
    boxes = [
        ("Problème", section_excerpt(dossier, "problem", 60)),
        ("Solution", section_excerpt(dossier, "solution", 60)),
        ("MVP", section_excerpt(dossier, "mvp", 60)),
    ]
    bw = (w - 160) // 3
    y = 120
    font = load_font(22, bold=True)
    small = load_font(18)
    for i, (label, body) in enumerate(boxes):
        x = 40 + i * (bw + 40)
        draw.rounded_rectangle(
            [(x, y), (x + bw, y + 400)], radius=12, fill=pal["card"], outline=pal["accent"]
        )
        draw.text((x + 16, y + 16), label, font=font, fill=pal["accent"])
        draw_wrapped(draw, body, (x + 16, y + 56), small, pal["text"], bw - 32)
        if i < 2:
            ax = x + bw + 8
            draw.line([(ax, y + 200), (ax + 24, y + 200)], fill=pal["accent"], width=2)
            draw.polygon(
                [(ax + 24, y + 195), (ax + 32, y + 200), (ax + 24, y + 205)],
                fill=pal["accent"],
            )
    draw.text((40, h - 50), "Pipeline produit — extrait sections dossier", font=small, fill=pal["muted"])
    return img


def render_moodboard(
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
    font = load_font(24, bold=True)
    small = load_font(18)
    draw.text((40, 520), "Identité visuelle", font=font, fill=pal["text"])
    visual = section_excerpt(dossier, "visual_identity", 300)
    draw_wrapped(draw, visual, (40, 560), small, pal["muted"], w - 80)
    return img


def render_finance_chart(
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
    font = load_font(22, bold=True)
    small = load_font(18)
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


RENDERERS: dict[str, Renderer] = {
    "hero": render_hero,
    "social_teaser": render_social_teaser,
    "mockup": render_mockup,
    "diagram": render_diagram,
    "moodboard": render_moodboard,
    "chart": render_finance_chart,
}
