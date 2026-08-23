"""Open ALNUA Hub UI as a desktop-like window.

On Windows we always use Edge/Chrome --app via launch-hub-app.ps1 so the
taskbar shows the ALNUA X icon (not pythonw). pywebview hosts the WebView in
the Python process → Windows taskbar = Python logo.
"""
from __future__ import annotations

import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
URL = "http://localhost:3000"
CREATE_NO_WINDOW = 0x08000000 if sys.platform == "win32" else 0


def _ready(timeout_s: int = 90) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(URL, timeout=3) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            pass
        time.sleep(2)
    return False


def _launch_edge_app() -> int:
    ps1 = ROOT / "scripts" / "launch-hub-app.ps1"
    if not ps1.is_file():
        print(f"Introuvable: {ps1}", file=sys.stderr)
        return 1
    subprocess.run(
        [
            "powershell.exe",
            "-NoProfile",
            "-NonInteractive",
            "-ExecutionPolicy",
            "Bypass",
            "-WindowStyle",
            "Hidden",
            "-File",
            str(ps1),
            "-Url",
            URL,
        ],
        check=False,
        creationflags=CREATE_NO_WINDOW,
    )
    return 0


def main() -> int:
    if not _ready():
        print(f"Hub web pas pret sur {URL}", file=sys.stderr)
        return 1
    # Windows: never host UI in pythonw (taskbar = Python icon).
    if sys.platform == "win32":
        return _launch_edge_app()

    try:
        import webview  # type: ignore
    except ImportError:
        return _launch_edge_app()

    webview.create_window(
        "ALNUA Hub",
        URL,
        width=1440,
        height=900,
        min_size=(1024, 700),
        confirm_close=False,
        background_color="#0E1014",
    )
    icon = ROOT / "assets" / "alnua-x-round.ico"
    if not icon.exists():
        icon = ROOT / "assets" / "alnua-hub.ico"
    kwargs: dict = {}
    if icon.exists():
        kwargs["icon"] = str(icon)
    webview.start(**kwargs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
