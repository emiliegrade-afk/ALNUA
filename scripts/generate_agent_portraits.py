"""Generate missing agent portrait PNGs (512) — stylized studio look via Pillow.

AI portraits preferred when available; this fills the roster so every AgentAvatar
has a file. Re-run after adding agents. Does not overwrite existing PNGs.
"""
from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
BUREAU = ROOT / "web" / "src" / "lib" / "agent-bureau.ts"
OUT = ROOT / "web" / "public" / "agents" / "portraits"

# Soft copper / ivory on obsidian — ALNUA brand
BG = (14, 16, 20)
RING = (224, 155, 106)
IVORY = (245, 242, 234)
MUTED = (167, 173, 181)


def _agents() -> list[tuple[str, str]]:
    text = BUREAU.read_text(encoding="utf-8")
    blocks = re.findall(
        r"\{\s*id:\s*\"([^\"]+)\",\s*room:[^}]*?name:\s*\"([^\"]+)\"",
        text,
        flags=re.DOTALL,
    )
    return [(aid, name) for aid, name in blocks]


def _initials(name: str) -> str:
    parts = [p for p in name.strip().split() if p]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def _tint(seed: str) -> tuple[int, int, int]:
    h = 0
    for ch in seed:
        h = (h * 31 + ord(ch)) & 0xFFFFFFFF
    variants = [
        (42, 28, 16),
        (46, 32, 21),
        (28, 31, 34),
        (36, 23, 8),
    ]
    return variants[h % len(variants)]


def make_portrait(agent_id: str, name: str) -> Image.Image:
    size = 512
    img = Image.new("RGB", (size, size), BG)
    draw = ImageDraw.Draw(img)
    base = _tint(agent_id)
    # Soft radial fill
    for r in range(size // 2, 0, -2):
        t = r / (size / 2)
        c = tuple(int(base[i] * t + BG[i] * (1 - t)) for i in range(3))
        draw.ellipse([size // 2 - r, size // 2 - r, size // 2 + r, size // 2 + r], fill=c)
    # Portrait oval suggestion
    draw.ellipse([140, 90, 372, 360], outline=RING, width=3)
    draw.ellipse([180, 130, 332, 300], fill=(base[0] + 20, base[1] + 12, base[2] + 8))
    # Ring
    draw.ellipse([24, 24, size - 24, size - 24], outline=RING, width=6)
    initials = _initials(name)
    try:
        font = ImageFont.truetype("arial.ttf", 96)
        font_sm = ImageFont.truetype("arial.ttf", 22)
    except OSError:
        font = ImageFont.load_default()
        font_sm = font
    bbox = draw.textbbox((0, 0), initials, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - tw) / 2, 200), initials, fill=IVORY, font=font)
    # Name caption
    nb = draw.textbbox((0, 0), name.split()[0], font=font_sm)
    nw = nb[2] - nb[0]
    draw.text(((size - nw) / 2, 400), name.split()[0], fill=MUTED, font=font_sm)
    return img


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    created = 0
    for agent_id, name in _agents():
        dest = OUT / f"{agent_id}.png"
        if dest.exists():
            continue
        make_portrait(agent_id, name).save(dest, "PNG")
        created += 1
        print(f"created {agent_id}")
    print(f"done — {created} new portraits")


if __name__ == "__main__":
    main()
