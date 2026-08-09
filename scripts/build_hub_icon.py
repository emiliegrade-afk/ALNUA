"""Build Windows .ico for ALNUA Hub shortcuts."""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
# Prefer the live brand mark; fall back to PWA icon-512.
SRC_CANDIDATES = (
    ROOT / "web" / "public" / "brand" / "alnua-mark.png",
    ROOT / "web" / "public" / "icon-512.png",
)
OUT = ROOT / "assets" / "alnua-hub.ico"
SIZES = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]


def main() -> None:
    source = next((p for p in SRC_CANDIDATES if p.exists()), None)
    if source is None:
        raise SystemExit(f"Missing icon source (tried: {', '.join(str(p) for p in SRC_CANDIDATES)})")

    base = Image.open(source).convert("RGBA")
    # Square crop for taskbar/desktop icons
    w, h = base.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    base = base.crop((left, top, left + side, top + side))

    images = [base.resize(size, Image.Resampling.LANCZOS) for size in SIZES]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    images[0].save(OUT, format="ICO", sizes=[(img.width, img.height) for img in images])
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
