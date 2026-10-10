"""Tiny HTML apps for Nadia Live — our templates only, then open in the browser."""

from __future__ import annotations

import html
import logging
import os
import re
import uuid
from pathlib import Path

from config.settings import get_settings
from services.input_sanitizer import sanitize_user_input

logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "live_html"

_HTML_RE = re.compile(
    r"\b(appli(?:cation)?\s+html|page\s+html|mini[-\s]?app|petite\s+appli|"
    r"cr[ée]e(?:r)?\s+une\s+appli|html\s+app)\b",
    re.IGNORECASE,
)
_KIND_KEYS = (
    ("timer", ("chrono", "minuteur", "timer", "compte à rebours")),
    ("counter", ("compteur", "counter", "compter")),
    ("checklist", ("checklist", "liste de tâches", "todo", "tâches")),
    ("notes", ("note", "bloc-notes", "notes")),
)


def wants_html_app(instruction: str) -> bool:
    return bool(_HTML_RE.search(instruction or ""))


def maybe_html(instruction: str) -> str | None:
    if not wants_html_app(instruction):
        return None
    return run_html_app(instruction)


def run_html_app(instruction: str) -> str:
    if not get_settings().live_pc_actions_enabled:
        return (
            "Je ne peux pas ouvrir une appli sur ce PC tant que "
            "LIVE_PC_ACTIONS_ENABLED n'est pas à 1."
        )
    brief = sanitize_user_input(instruction, max_length=240, redact_pii_enabled=False).strip()
    kind = _kind(brief)
    title = _title(brief, kind)
    path = _write(kind, title, brief)
    _reveal(path)
    from services.live_cards_format import list_card

    return list_card(
        f"Appli {kind}",
        [f"Ouverte : {path.name}", str(path)],
        lead=f"Petite appli « {title} » ouverte dans le navigateur (bac à sable Hub).",
    )


def _kind(brief: str) -> str:
    lower = brief.lower()
    for kind, keys in _KIND_KEYS:
        if any(k in lower for k in keys):
            return kind
    return "notes"


def _title(brief: str, kind: str) -> str:
    labels = {
        "timer": "Chrono",
        "counter": "Compteur",
        "checklist": "Checklist",
        "notes": "Notes",
    }
    return labels[kind]


def _write(kind: str, title: str, brief: str) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    name = f"{kind}-{uuid.uuid4().hex[:8]}.html"
    path = OUT_DIR / name
    path.write_text(_page(kind, title, brief), encoding="utf-8")
    return path


def _page(kind: str, title: str, brief: str) -> str:
    safe_title = html.escape(title)
    safe_brief = html.escape(brief[:200])
    widget = {
        "timer": (
            '<p id="t">00:00</p><button type="button" id="go">Start / pause</button>'
            "<script>let s=0,on=0,iv;const el=document.getElementById('t');"
            "document.getElementById('go').onclick=()=>{on=!on;if(on){iv=setInterval(()=>{"
            "s++;el.textContent=String(Math.floor(s/60)).padStart(2,'0')+':'"
            "+String(s%60).padStart(2,'0');},1000);}else clearInterval(iv);};</script>"
        ),
        "counter": (
            '<p id="n">0</p><button type="button" id="m">−</button>'
            '<button type="button" id="p">+</button>'
            "<script>let n=0;const el=document.getElementById('n');"
            "document.getElementById('p').onclick=()=>el.textContent=++n;"
            "document.getElementById('m').onclick=()=>el.textContent=--n;</script>"
        ),
        "checklist": (
            '<input id="i" placeholder="Élément"><button type="button" id="a">Ajouter</button>'
            '<ul id="l"></ul><script>document.getElementById("a").onclick=()=>{'
            "const v=document.getElementById('i').value.trim();if(!v)return;"
            "const li=document.createElement('li');li.textContent=v;"
            "document.getElementById('l').appendChild(li);};</script>"
        ),
        "notes": (
            f"<p>{safe_brief}</p>"
            '<textarea rows="10" style="width:100%" placeholder="Écris ici…"></textarea>'
        ),
    }[kind]
    return (
        "<!DOCTYPE html><html lang=\"fr\"><head><meta charset=\"utf-8\">"
        f"<title>{safe_title}</title>"
        "<style>body{font-family:sans-serif;background:#111;color:#eee;padding:2rem;max-width:40rem}"
        "button{margin:.4rem;padding:.4rem .8rem}textarea{background:#222;color:#eee}</style>"
        f"</head><body><h1>{safe_title}</h1>{widget}</body></html>"
    )


def _reveal(path: Path) -> None:
    import webbrowser

    opened = webbrowser.open(path.resolve().as_uri())
    if opened:
        return
    if os.name == "nt":
        os.startfile(str(path))  # noqa: S606 — file we just wrote under data/live_html
        return
    import subprocess

    subprocess.Popen(["xdg-open", str(path)], shell=False)  # noqa: S603
