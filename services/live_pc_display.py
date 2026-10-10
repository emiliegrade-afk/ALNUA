"""Place the last allowlisted window on a chosen monitor (DEC-044)."""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)

_SCREEN_NUM = re.compile(
    r"(?:sur\s+)?(?:l['’])?(?:écran|ecran|monitor)\s*(?:n[o°]?\s*)?(\d+)",
    re.IGNORECASE,
)
_LEFT = re.compile(r"\b(?:à|a)\s+gauche\b", re.IGNORECASE)
_RIGHT = re.compile(r"\b(?:à|a)\s+droite\b", re.IGNORECASE)

WINDOW_HINTS: dict[str, tuple[str, ...]] = {
    "instagram": ("instagram",),
    "gmail": ("gmail", "mail"),
    "calendar": ("calendar", "agenda"),
    "youtube": ("youtube",),
    "discord": ("discord",),
    "linkedin": ("linkedin",),
    "github": ("github",),
    "notion": ("notion",),
    "chrome": ("chrome",),
    "edge": ("edge",),
}


@dataclass(frozen=True)
class Display:
    index: int
    left: int
    top: int
    right: int
    bottom: int

    @property
    def label(self) -> str:
        return str(self.index)


def parse_screen(instruction: str) -> int | None:
    """1-based screen index, or None if the phrase does not pick a display."""
    text = instruction or ""
    match = _SCREEN_NUM.search(text)
    if match:
        num = int(match.group(1))
        return num if num >= 1 else None
    displays = list_displays()
    if not displays:
        return None
    ordered = sorted(displays, key=lambda d: d.left)
    if _LEFT.search(text):
        return ordered[0].index
    if _RIGHT.search(text):
        return ordered[-1].index
    return None


def list_displays() -> list[Display]:
    if os.name != "nt":
        return [Display(1, 0, 0, 1920, 1080)]
    return _win_displays()


def place_last_window(screen_index: int, hint: str = "") -> str:
    displays = {d.index: d for d in list_displays()}
    target = displays.get(screen_index)
    if target is None:
        known = ", ".join(str(i) for i in sorted(displays))
        return f"Écran {screen_index} introuvable ({known or 'aucun'})."
    hwnd = find_window(hint)
    if not hwnd:
        return (
            f"Page ouverte, mais je n'ai pas trouvé la fenêtre "
            f"« {hint or 'navigateur'} » à déplacer."
        )
    move_window(hwnd, target)
    return f"Fenêtre placée sur l'écran {target.label}."


def find_window(hint: str) -> int:
    needles = WINDOW_HINTS.get(hint.lower(), (hint.lower(),) if hint else ())
    if not needles:
        needles = ("chrome", "edge", "firefox")
    return _find_hwnd(needles)


def move_window(hwnd: int, display: Display) -> None:
    if os.name != "nt":
        return
    import ctypes

    user32 = ctypes.windll.user32
    width = max(800, display.right - display.left - 40)
    height = max(600, display.bottom - display.top - 40)
    user32.MoveWindow(hwnd, display.left + 20, display.top + 20, width, height, True)
    user32.SetForegroundWindow(hwnd)


def _win_displays() -> list[Display]:
    import ctypes
    from ctypes import wintypes

    found: list[Display] = []

    class RECT(ctypes.Structure):
        _fields_ = [
            ("left", wintypes.LONG),
            ("top", wintypes.LONG),
            ("right", wintypes.LONG),
            ("bottom", wintypes.LONG),
        ]

    def _cb(hmon, hdc, lprc, lparam):  # noqa: ARG001
        rect = ctypes.cast(lprc, ctypes.POINTER(RECT)).contents
        found.append(
            Display(
                index=len(found) + 1,
                left=int(rect.left),
                top=int(rect.top),
                right=int(rect.right),
                bottom=int(rect.bottom),
            )
        )
        return 1

    mon_enum = ctypes.WINFUNCTYPE(
        ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong, ctypes.POINTER(RECT), ctypes.c_long
    )
    ctypes.windll.user32.EnumDisplayMonitors(0, 0, mon_enum(_cb), 0)
    return found or [Display(1, 0, 0, 1920, 1080)]


def _find_hwnd(needles: tuple[str, ...]) -> int:
    if os.name != "nt":
        return 0
    import ctypes
    from ctypes import wintypes

    matches: list[int] = []

    def _cb(hwnd, lparam):  # noqa: ARG001
        if not ctypes.windll.user32.IsWindowVisible(hwnd):
            return True
        buf = ctypes.create_unicode_buffer(512)
        ctypes.windll.user32.GetWindowTextW(hwnd, buf, 512)
        title = (buf.value or "").lower()
        if any(n in title for n in needles if n):
            matches.append(int(hwnd))
        return True

    wenum = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    ctypes.windll.user32.EnumWindows(wenum(_cb), 0)
    return matches[-1] if matches else 0


def wait_then_place(screen_index: int, hint: str, *, delay: float = 1.2) -> str:
    time.sleep(delay)
    return place_last_window(screen_index, hint)
