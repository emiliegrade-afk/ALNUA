"""Confirmed click / type on allowlisted windows only (DEC-044). Never free computer-use."""

from __future__ import annotations

import logging
import os
import re
import uuid
from dataclasses import dataclass
from typing import Any

from config.settings import get_settings
from services.input_sanitizer import sanitize_user_input
from services.live_cards_format import draft_card
from services.live_pc_display import WINDOW_HINTS, find_window, parse_screen

logger = logging.getLogger(__name__)

_TYPE_RE = re.compile(
    r"\b(?:tape|taper|écris|ecris|saisis|frappe)\b(?:\s+(?:dans|sur))?",
    re.IGNORECASE,
)
_CLICK_RE = re.compile(r"\b(?:clique|cliquer|click)\b", re.IGNORECASE)
_CONFIRM_KEYS = (
    "valide le clic",
    "valide la frappe",
    "valide le tap",
    "fais le clic",
    "tape maintenant",
)
_IN_WIN = re.compile(
    r"\b(?:dans|sur)\s+(instagram|gmail|youtube|discord|linkedin|github|notion|calendar|chrome|edge)\b",
    re.IGNORECASE,
)
_QUOTED = re.compile(r"[«\"']([^»\"']{1,200})[»\"']")


@dataclass
class InputDraft:
    id: str
    kind: str  # type | click
    window: str
    text: str
    screen: int | None


_drafts: dict[str, InputDraft] = {}
_last_id: str | None = None


def wants_pc_input(instruction: str) -> bool:
    text = instruction or ""
    return bool(_TYPE_RE.search(text) or _CLICK_RE.search(text))


def wants_pc_confirm(instruction: str) -> bool:
    n = (instruction or "").lower()
    return any(k in n for k in _CONFIRM_KEYS)


def maybe_pc_input(instruction: str) -> str | None:
    if wants_pc_confirm(instruction):
        return execute_latest()
    if not wants_pc_input(instruction):
        return None
    return propose_input(instruction)


def propose_input(instruction: str) -> str:
    if not get_settings().live_pc_actions_enabled:
        return (
            "Clic et frappe sont coupés (LIVE_PC_ACTIONS_ENABLED). "
            "Même activés : Valider obligatoire, fenêtre liste blanche seulement."
        )
    parsed = parse_input(instruction)
    if parsed is None:
        return (
            "Je ne clique/tape que dans une fenêtre connue "
            "(Instagram, Gmail, Discord…). "
            "Exemple : « tape bonjour dans Discord » ou « clique au centre sur Gmail »."
        )
    _drafts[parsed.id] = parsed
    global _last_id
    _last_id = parsed.id
    action = "Taper" if parsed.kind == "type" else "Cliquer au centre"
    where = parsed.window
    extra = f" — écran {parsed.screen}" if parsed.screen else ""
    body = f"{action} « {parsed.text} » dans {where}{extra}" if parsed.kind == "type" else (
        f"{action} de la fenêtre {where}{extra}"
    )
    return draft_card(
        kind="pc_input",
        title="Action PC à valider",
        body=body,
        draft_id=parsed.id,
        lead="Rien n'est tapé ni cliqué tant que tu n'as pas validé (DEC-044).",
    )


def parse_input(instruction: str) -> InputDraft | None:
    text = sanitize_user_input(instruction or "", max_length=240, redact_pii_enabled=False)
    win_match = _IN_WIN.search(text)
    window = (win_match.group(1) if win_match else "").lower()
    if window not in WINDOW_HINTS:
        return None
    screen = parse_screen(text)
    if _TYPE_RE.search(text):
        typed = _extract_typed(text, window)
        if not typed:
            return None
        return InputDraft(id=uuid.uuid4().hex[:16], kind="type", window=window, text=typed, screen=screen)
    if _CLICK_RE.search(text):
        return InputDraft(id=uuid.uuid4().hex[:16], kind="click", window=window, text="centre", screen=screen)
    return None


def _extract_typed(text: str, _window: str) -> str:
    quoted = _QUOTED.search(text)
    if quoted:
        return quoted.group(1).strip()[:200]
    cleaned = _TYPE_RE.sub("", text, count=1)
    cleaned = _IN_WIN.sub("", cleaned)
    cleaned = re.sub(r"(?:sur\s+)?(?:l['’])?(?:écran|ecran)\s*\d+", "", cleaned, flags=re.I)
    return cleaned.strip(" .,;:-")[:200]


def execute_input(draft_id: str) -> dict[str, Any]:
    draft = _drafts.get(draft_id)
    if draft is None:
        return {"success": False, "message": "Aucune action PC en attente avec cet id."}
    if not get_settings().live_pc_actions_enabled:
        return {"success": False, "message": "LIVE_PC_ACTIONS_ENABLED n'est pas à 1."}
    hwnd = find_window(draft.window)
    if not hwnd:
        return {
            "success": False,
            "message": f"Fenêtre « {draft.window} » introuvable — ouvre-la d'abord.",
        }
    if draft.kind == "type":
        _type_into(hwnd, draft.text)
        _forget(draft_id)
        return {"success": True, "message": f"Texte tapé dans {draft.window}."}
    _click_center(hwnd)
    _forget(draft_id)
    return {"success": True, "message": f"Clic au centre de {draft.window}."}


def execute_latest() -> str:
    if not _last_id:
        return "Aucune action PC en attente. Dis d'abord « tape … dans Discord »."
    out = execute_input(_last_id)
    return str(out.get("message") or "Action impossible.")


def latest_input_id() -> str | None:
    return _last_id


def reset_for_tests() -> None:
    global _last_id
    _drafts.clear()
    _last_id = None


def _forget(draft_id: str) -> None:
    global _last_id
    _drafts.pop(draft_id, None)
    if _last_id == draft_id:
        _last_id = None


def _type_into(hwnd: int, text: str) -> None:
    if os.name != "nt":
        return
    import ctypes

    user32 = ctypes.windll.user32
    user32.SetForegroundWindow(hwnd)
    for char in text:
        user32.PostMessageW(hwnd, 0x0102, ord(char), 0)  # WM_CHAR


def _click_center(hwnd: int) -> None:
    if os.name != "nt":
        return
    import ctypes
    from ctypes import wintypes

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    rect = RECT()
    user32 = ctypes.windll.user32
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    x = (rect.left + rect.right) // 2
    y = (rect.top + rect.bottom) // 2
    user32.SetCursorPos(x, y)
    user32.mouse_event(0x0002, 0, 0, 0, 0)  # LEFTDOWN
    user32.mouse_event(0x0004, 0, 0, 0, 0)  # LEFTUP
