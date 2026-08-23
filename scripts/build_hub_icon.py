"""Build Windows .ico — X rond ALNUA (format BMP classique multi-tailles).

Pillow ICO souvent n'expose qu'une frame ; le shell Windows lit mieux
un ICO BITMAP 32-bit + masque AND (coins vraiment transparents).
"""
from __future__ import annotations

import struct
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
SRC_CANDIDATES = (
    ROOT / "web" / "public" / "brand" / "alnua-mark.png",
    ROOT / "assets" / "brand" / "reference-logo-principal-icone.png",
)
OUT_PRIMARY = ROOT / "assets" / "alnua-x-round.ico"
OUT_LEGACY = ROOT / "assets" / "alnua-hub.ico"
SIZES = (256, 128, 64, 48, 32, 16)


def _square_crop(im: Image.Image) -> Image.Image:
    w, h = im.size
    side = min(w, h)
    left = (w - side) // 2
    top = (h - side) // 2
    return im.crop((left, top, left + side, top + side))


def _hard_circle_mask(size: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    inset = 1 if size >= 32 else 0
    draw.ellipse((inset, inset, size - 1 - inset, size - 1 - inset), fill=255)
    return mask


def _circle_frame(master: Image.Image, size: int) -> Image.Image:
    fr = master.resize((size, size), Image.Resampling.LANCZOS)
    circle = _hard_circle_mask(size)
    r, g, b, a = fr.split()
    a = Image.composite(a, Image.new("L", fr.size, 0), circle)
    return Image.merge("RGBA", (r, g, b, a))


def _prepare(source: Path) -> Image.Image:
    base = Image.open(source).convert("RGBA")
    base = _square_crop(base)
    master = base.resize((512, 512), Image.Resampling.LANCZOS)
    circle = _hard_circle_mask(512)
    r, g, b, a = master.split()
    a = Image.composite(a, Image.new("L", master.size, 0), circle)
    return Image.merge("RGBA", (r, g, b, a))


def _ico_bmp_bytes(im: Image.Image) -> bytes:
    """32-bit BMP (BITMAPINFOHEADER + XOR BGRA bottom-up) + 1-bit AND mask."""
    size = im.width
    header = struct.pack(
        "<IIIHHIIIIII",
        40,
        size,
        size * 2,
        1,
        32,
        0,
        size * size * 4,
        0,
        0,
        0,
        0,
    )
    pixels = im.load()
    xor = bytearray()
    for y in range(size - 1, -1, -1):
        for x in range(size):
            r, g, b, a = pixels[x, y]
            xor += bytes((b, g, r, a))

    row_bytes = ((size + 31) // 32) * 4
    and_mask = bytearray()
    for y in range(size - 1, -1, -1):
        row = 0
        bits = 0
        row_data = bytearray()
        for x in range(size):
            a = pixels[x, y][3]
            bit = 1 if a < 128 else 0
            row = (row << 1) | bit
            bits += 1
            if bits == 8:
                row_data.append(row)
                row = 0
                bits = 0
        if bits:
            row_data.append(row << (8 - bits))
        while len(row_data) < row_bytes:
            row_data.append(0)
        and_mask += row_data
    return header + bytes(xor) + bytes(and_mask)


def _write_ico(master: Image.Image, out: Path) -> None:
    frames = [_circle_frame(master, s) for s in SIZES]
    corner = frames[0].getpixel((0, 0))
    if corner[3] != 0:
        raise SystemExit(f"Corner not transparent on {out}: {corner}")

    payloads = [_ico_bmp_bytes(fr) for fr in frames]
    count = len(SIZES)
    buf = bytearray()
    buf += struct.pack("<HHH", 0, 1, count)
    offset = 6 + 16 * count
    entries: list[tuple[int, int, int, int]] = []
    for size, data in zip(SIZES, payloads):
        bw = 0 if size >= 256 else size
        bh = 0 if size >= 256 else size
        entries.append((bw, bh, len(data), offset))
        offset += len(data)
    for bw, bh, nbytes, off in entries:
        buf += struct.pack("<BBBBHHII", bw, bh, 0, 0, 1, 32, nbytes, off)
    for data in payloads:
        buf += data

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(buf)
    print(f"Wrote {out} ({count} sizes, {len(buf)} bytes)")


def main() -> None:
    source = next((p for p in SRC_CANDIDATES if p.exists()), None)
    if source is None:
        raise SystemExit(
            f"Missing round mark (tried: {', '.join(str(p) for p in SRC_CANDIDATES)})"
        )
    print(f"Source: {source}")
    master = _prepare(source)
    _write_ico(master, OUT_PRIMARY)
    _write_ico(master, OUT_LEGACY)
    preview = ROOT / "assets" / "alnua-x-round-preview.png"
    master.resize((256, 256), Image.Resampling.LANCZOS).save(preview)
    print(f"Preview: {preview}")

    # Web / PWA / favicon — same round mark (not the old square icons)
    web_public = ROOT / "web" / "public"
    web_app = ROOT / "web" / "src" / "app"
    for name, size in (
        ("icon-192.png", 192),
        ("icon-512.png", 512),
        ("apple-touch-icon.png", 180),
        ("favicon-32.png", 32),
    ):
        fr = _circle_frame(master, size)
        out = web_public / name
        fr.save(out, "PNG")
        print(f"Wrote {out}")

    # Next.js App Router picks these automatically for tab + taskbar favicons
    if web_app.is_dir():
        for name, size in (("icon.png", 512), ("apple-icon.png", 180)):
            fr = _circle_frame(master, size)
            out = web_app / name
            fr.save(out, "PNG")
            print(f"Wrote {out}")

    favicon = web_public / "favicon.ico"
    favicon.write_bytes(OUT_PRIMARY.read_bytes())
    app_fav = web_app / "favicon.ico"
    if app_fav.parent.exists():
        app_fav.write_bytes(OUT_PRIMARY.read_bytes())
        print(f"Wrote {app_fav}")
    print(f"Wrote {favicon}")


if __name__ == "__main__":
    main()
