"""R&D deck — minimal markdown to HTML conversion."""

from __future__ import annotations

import html
import re

_PLACEHOLDER_PREFIXES = (
    "_À compléter",
    "_Business case à générer",
    "_Risques à identifier",
)


def is_placeholder(content: str) -> bool:
    t = (content or "").strip()
    if not t or len(t) < 20:
        return True
    return any(t.startswith(p) for p in _PLACEHOLDER_PREFIXES)


def md_to_html(md: str) -> str:
    """Minimal markdown → HTML (no external deps)."""
    if not md.strip():
        return ""

    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    in_ul = False
    in_ol = False

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def inline(text: str) -> str:
        text = html.escape(text)
        text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
        text = re.sub(r"\*(.+?)\*", r"<em>\1</em>", text)
        text = re.sub(r"`(.+?)`", r"<code>\1</code>", text)
        return text

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            close_lists()
            continue

        hm = re.match(r"^(#{1,4})\s+(.+)$", line)
        if hm:
            close_lists()
            level = len(hm.group(1))
            out.append(f"<h{level}>{inline(hm.group(2))}</h{level}>")
            continue

        if re.match(r"^[-*]\s+", line):
            if not in_ul:
                close_lists()
                in_ul = True
                out.append("<ul>")
            out.append(f"<li>{inline(re.sub(r'^[-*]\s+', '', line))}</li>")
            continue

        if re.match(r"^\d+\.\s+", line):
            if not in_ol:
                close_lists()
                in_ol = True
                out.append("<ol>")
            out.append(f"<li>{inline(re.sub(r'^\d+\.\s+', '', line))}</li>")
            continue

        close_lists()
        out.append(f"<p>{inline(line)}</p>")

    close_lists()
    return "\n".join(out)
