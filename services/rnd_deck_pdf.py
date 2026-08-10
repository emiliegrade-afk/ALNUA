"""R&D deck — HTML to PDF export (Playwright / headless browser)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def relative_path(path: Path | None, repo_root: Path) -> str | None:
    if path is None:
        return None
    try:
        return path.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    """HTML → PDF: Edge/Chrome on Windows (no install), Playwright elsewhere."""
    errors: list[str] = []

    if sys.platform == "win32":
        try:
            html_to_pdf_headless_browser(html_path, pdf_path)
            return
        except Exception as exc:
            errors.append(f"Edge/Chrome: {exc}")

    try:
        html_to_pdf_playwright(html_path, pdf_path)
        return
    except Exception as exc:
        errors.append(f"Playwright: {exc}")

    if sys.platform != "win32":
        try:
            html_to_pdf_headless_browser(html_path, pdf_path)
            return
        except Exception as exc:
            errors.append(f"Navigateur headless: {exc}")

    raise RuntimeError(
        "Export PDF impossible. "
        + " ; ".join(errors)
        + " — Ouvre le HTML et Ctrl+P → Enregistrer en PDF."
    )


def html_to_pdf_playwright(html_path: Path, pdf_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    file_url = html_path.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.goto(file_url, wait_until="networkidle")
            page.pdf(
                path=str(pdf_path),
                format="A4",
                landscape=True,
                print_background=True,
                margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            )
        finally:
            browser.close()


def html_to_pdf_headless_browser(html_path: Path, pdf_path: Path) -> None:
    """Windows fallback: Edge or Chrome --headless --print-to-pdf."""
    if sys.platform != "win32":
        raise RuntimeError("fallback Windows uniquement")

    candidates = [
        os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"),
        os.path.expandvars(r"%ProgramFiles%\Google\Chrome\Application\chrome.exe"),
        os.path.expandvars(r"%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe"),
    ]
    exe = next((p for p in candidates if p and Path(p).is_file()), None)
    if not exe:
        raise RuntimeError("Edge/Chrome introuvable")

    file_url = html_path.resolve().as_uri()
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    if pdf_path.exists():
        pdf_path.unlink()

    result = subprocess.run(
        [
            exe,
            "--headless=new",
            "--disable-gpu",
            f"--print-to-pdf={pdf_path.resolve()}",
            file_url,
        ],
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0 or not pdf_path.is_file():
        detail = (result.stderr or result.stdout or "").strip()[:200]
        raise RuntimeError(detail or f"code {result.returncode}")
