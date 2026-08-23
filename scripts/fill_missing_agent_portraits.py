"""Replace Pillow monogram stubs with photoreal AI portraits via OpenRouter Images API.

Only overwrites files under SIZE_CAP bytes (stubs). Real portraits are left alone.
Usage:
  python scripts/fill_missing_agent_portraits.py
  python scripts/fill_missing_agent_portraits.py --only ads,controller
  python scripts/fill_missing_agent_portraits.py --dry-run
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "web" / "public" / "agents" / "portraits"
BUREAU = ROOT / "web" / "src" / "lib" / "agent-bureau.ts"
SIZE_CAP = 100_000  # stubs are ~18–26 KB; real portraits are >1 MB
MODEL = os.getenv("ALNUA_PORTRAIT_MODEL", "google/gemini-2.5-flash-image")
API_URL = "https://openrouter.ai/api/v1/images"

# Soft appearance cues — diversity aligned with existing real roster photos.
APPEARANCE: dict[str, str] = {
    "ads": "French man early 30s, short brown hair, light stubble, smart casual dark shirt",
    "ai_programmer": "Japanese man early 30s, neat black hair, thin-frame glasses, dark turtleneck",
    "analyst_data": "French man late 20s, short ash-brown hair, clean shaven, charcoal shirt",
    "brand": "French woman early 30s, auburn hair in a low bun, minimal makeup, black blouse",
    "coding_coach": "French-Italian man mid 30s, warm smile, short wavy brown hair, navy knit",
    "content_app": "West African French woman late 20s, natural curls, radiant smile, black top",
    "content_company": "Belgian woman early 30s, blonde bob, calm expression, charcoal blazer",
    "content_gaming": "androgynous person late 20s, silver-tipped dark hair, edgy techwear black",
    "content_robo": "Scandinavian woman early 30s, blonde hair pulled back, cool gaze, black jacket",
    "controller": "French man mid 30s, short dark hair, precise look, charcoal suit no tie",
    "dev_gaming": "woman late 20s, platinum blonde short hair, playful smirk, dark hoodie under blazer",
    "dev_integrator": "West African man early 30s, short fade, confident, black crewneck",
    "electronics": "Portuguese man mid 30s, dark curly hair, trimmed beard, dark polo",
    "embedded_dev": "South Asian woman early 30s, long black hair, focused, black turtleneck",
    "environment_artist": "South Asian woman late 20s, long dark hair, soft expression, dark knit",
    "firmware": "German woman mid 30s, short ash-blonde hair, sharp features, black shirt",
    "hardware": "Japanese woman early 30s, black bob, calm precision, dark blazer",
    "industrial_design": "Swedish woman early 30s, light brown hair, serene, minimal black top",
    "level_designer": "Nordic man late 20s, blond hair, friendly, charcoal hoodie",
    "mechanical": "South Asian man mid 30s, short black hair, thoughtful, dark work shirt",
    "narrative_designer": "woman early 30s, dark wavy hair, literary vibe, black turtleneck",
    "qa_gaming": "Brazilian man late 20s, short curly dark hair, warm smile, dark tee",
    "qa_robot": "Levantine man early 30s, short black hair, serious, charcoal shirt",
    "rnd_agent": "man mid 30s, short brown hair, intense researcher look, black blazer",
    "rnd_ceo": "French man early 30s, dark hair, polished, charcoal suit jacket",
    "rnd_committee": "French woman early 30s, chestnut hair, warm facilitator smile, black blouse",
    "rnd_dossier": "French woman late 20s, dark hair, precise analyst look, charcoal blazer",
    "rnd_product": "French man late 20s, curly brown hair, approachable, dark shirt",
    "rnd_social": "French woman late 20s, light brown hair, bright smile, black top",
    "rnd_visual": "French man early 30s, dark hair, creative look, black shirt",
    "safety": "French woman mid 30s, blonde hair tied back, calm authority, dark blazer",
    "simulation": "Japanese man early 30s, neat black hair, soft smile, charcoal sweater",
    "sound_designer": "Nordic woman mid 30s, strawberry-blonde hair, quiet focus, black knit",
    "technical_artist": "Austrian man mid 30s, light brown hair, beard stubble, dark shirt",
    "vfx_artist": "Latino man early 30s, short dark hair, energetic, black crewneck",
    "vision_ai": "West African woman early 30s, braided hair up, sharp gaze, black blazer",
}


def _load_dotenv() -> None:
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v


def _agents() -> dict[str, tuple[str, str]]:
    text = BUREAU.read_text(encoding="utf-8")
    out: dict[str, tuple[str, str]] = {}
    for m in re.finditer(
        r'id:\s*"([^"]+)".*?name:\s*"([^"]+)".*?role:\s*"([^"]+)"',
        text,
        flags=re.DOTALL,
    ):
        out[m.group(1)] = (m.group(2), m.group(3))
    return out


def _prompt(agent_id: str, name: str, role: str) -> str:
    look = APPEARANCE.get(
        agent_id,
        f"professional adult matching the name {name}, diverse realistic features",
    )
    return (
        "Photorealistic corporate headshot portrait, square 1:1, head and shoulders, "
        "face centered in upper third, looking at camera, natural skin texture, "
        "clean studio lighting, solid pure void black background (#000000), "
        "no text, no watermark, no logo, no nameplate, no props, "
        f"{look}. Role vibe: {role}. Premium tech company aesthetic like Apple/Dyson."
    )


def _generate(api_key: str, prompt: str) -> bytes:
    body = {
        "model": MODEL,
        "prompt": prompt,
        "aspect_ratio": "1:1",
        "output_format": "png",
        "resolution": "1K",
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://alnua.local",
            "X-Title": "ALNUA Hub portraits",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        payload = json.loads(resp.read().decode("utf-8"))

    data = payload.get("data") or []
    if not data:
        raise RuntimeError(f"empty image response: {payload!r}"[:400])
    item = data[0]
    b64 = item.get("b64_json") or item.get("b64")
    if not b64 and isinstance(item.get("url"), str) and item["url"].startswith("data:"):
        b64 = item["url"].split(",", 1)[-1]
    if not b64:
        url = item.get("url")
        if isinstance(url, str) and url.startswith("http"):
            with urllib.request.urlopen(url, timeout=120) as img_resp:
                return img_resp.read()
        raise RuntimeError(f"no image bytes in response keys={list(item)}"[:300])
    return base64.b64decode(b64)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", default="", help="Comma-separated agent ids")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force-all-stubs", action="store_true", default=True)
    args = parser.parse_args()

    _load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key and not args.dry_run:
        print("OPENROUTER_API_KEY missing", file=sys.stderr)
        return 1

    roster = _agents()
    only = {x.strip() for x in args.only.split(",") if x.strip()}
    targets: list[str] = []
    for path in sorted(OUT.glob("*.png")):
        aid = path.stem
        if only and aid not in only:
            continue
        if path.stat().st_size >= SIZE_CAP:
            continue
        if aid not in roster:
            print(f"skip orphan {aid}")
            continue
        targets.append(aid)

    print(f"model={MODEL} targets={len(targets)}")
    if args.dry_run:
        for aid in targets:
            name, role = roster[aid]
            print(f"  {aid}: {name} — {role}")
        return 0

    ok = 0
    fail = 0
    for i, aid in enumerate(targets, 1):
        name, role = roster[aid]
        dest = OUT / f"{aid}.png"
        prompt = _prompt(aid, name, role)
        print(f"[{i}/{len(targets)}] {aid} ({name})…", flush=True)
        try:
            png = _generate(api_key, prompt)
            if len(png) < 5_000:
                raise RuntimeError(f"image too small ({len(png)} bytes)")
            dest.write_bytes(png)
            print(f"  wrote {dest.name} ({len(png)} bytes)")
            ok += 1
        except (urllib.error.HTTPError, urllib.error.URLError, RuntimeError, OSError) as exc:
            detail = str(exc)
            if isinstance(exc, urllib.error.HTTPError):
                try:
                    detail = exc.read().decode("utf-8", errors="replace")[:400]
                except Exception:
                    pass
            print(f"  FAIL {aid}: {detail}", file=sys.stderr)
            fail += 1
            time.sleep(2)
            continue
        time.sleep(0.6)

    print(f"done ok={ok} fail={fail}")
    return 0 if fail == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
