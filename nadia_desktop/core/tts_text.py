"""Normalize assistant text before TTS — natural spoken French, no robot artifacts."""

from __future__ import annotations

import re
import unicodedata

# Classic text emoticons / smileys (read aloud as "deux points parenthèse").
_TEXT_SMILEY_RE = re.compile(
    r"(?<!\w)"
    r"(?:"
    r"[:;=8][\-~]?[)\]DpP3oO/\\|]"
    r"|(?:[xX][\-~]?[Dd])"
    r"|\(\s*[xX]\s*\)"
    r"|<3"
    r")"
    r"(?!\w)"
)

# Unicode emoji blocks + dingbats + symbols often read literally.
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\U00002600-\U000027BF"
    "\U0001F1E0-\U0001F1FF"
    "\U000024C2-\U0001F251"
    "\U0000FE00-\U0000FE0F"
    "\U0000200D"
    "]+",
    flags=re.UNICODE,
)


def _strip_emoji(text: str) -> str:
    cleaned = _EMOJI_RE.sub(" ", text)
    # Fallback: remove remaining symbols marked as emoji presentation.
    out: list[str] = []
    for ch in cleaned:
        if unicodedata.category(ch) in {"So", "Sk", "Sm"} and ord(ch) > 0x2600:
            continue
        out.append(ch)
    return "".join(out)


def prepare_text_for_speech(text: str, *, max_chars: int = 900) -> str:
    """
    Turn LLM/markdown chat text into something Edge TTS can read naturally.

    Removes emojis, markdown, URLs, and punctuation that sounds robotic in FR.
    """
    if not text or not text.strip():
        return ""

    t = text.strip()

    # Code blocks / inline code
    t = re.sub(r"```[\s\S]*?```", " ", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)

    # Markdown links [label](url) → label only
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)

    # Bold / italic / strike
    t = re.sub(r"\*{1,3}([^*]+)\*{1,3}", r"\1", t)
    t = re.sub(r"_{1,2}([^_]+)_{1,2}", r"\1", t)
    t = re.sub(r"~~([^~]+)~~", r"\1", t)

    # Headings / blockquotes
    t = re.sub(r"^#{1,6}\s*", "", t, flags=re.MULTILINE)
    t = re.sub(r"^>\s*", "", t, flags=re.MULTILINE)

    # List markers
    t = re.sub(r"^\s*[-•*]\s+", "", t, flags=re.MULTILINE)
    t = re.sub(r"^\s*\d+[.)]\s+", "", t, flags=re.MULTILINE)

    # URLs and handles (often spelled letter-by-letter)
    t = re.sub(r"https?://\S+", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"www\.\S+", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"@[\w.-]+", " ", t)
    t = re.sub(r"#[\w-]+", " ", t)

    # Emojis + ASCII smileys
    t = _strip_emoji(t)
    t = _TEXT_SMILEY_RE.sub(" ", t)

    # Remaining markdown / UI punctuation
    t = re.sub(r"[#*_~>|\\[\]{}]", " ", t)

    # Punctuation that Edge reads literally in French
    t = t.replace("…", ".")
    t = re.sub(r"\.{2,}", ".", t)
    t = re.sub(r"!+", "!", t)
    t = re.sub(r"\?+", "?", t)
    t = re.sub(r"[:;]", ",", t)
    t = re.sub(r"[—–]", ", ", t)
    t = re.sub(r"\(\s*([^)]{1,120})\s*\)", r", \1, ", t)

    # Spoken replacements
    t = t.replace("&", " et ")
    t = re.sub(r"(\d)\s*%", r"\1 pour cent", t)
    t = re.sub(r"\bvs\.?\b", " contre ", t, flags=re.IGNORECASE)
    t = re.sub(r"\be\.g\.\b", " par exemple ", t, flags=re.IGNORECASE)
    t = re.sub(r"\bi\.e\.\b", " c'est-à-dire ", t, flags=re.IGNORECASE)

    # Newlines → short pauses
    t = re.sub(r"\n+", ". ", t)

    # Collapse whitespace and stray punctuation clusters
    t = re.sub(r"\s+", " ", t)
    t = re.sub(r"\s*([,.!?])\s*", r"\1 ", t)
    t = re.sub(r"([,.!?]){2,}", r"\1", t)
    t = re.sub(r"\s+,", ",", t)
    t = re.sub(r",\s*,+", ", ", t)
    t = re.sub(r"\.\s*\.", ".", t)

    t = t.strip(" ,.;:!?")

    if len(t) > max_chars:
        t = t[:max_chars]
        cut = max(t.rfind("."), t.rfind("?"), t.rfind("!"))
        if cut > max_chars // 2:
            t = t[: cut + 1]

    return t.strip()


def split_for_speech(text: str, *, max_chunk: int = 220) -> list[str]:
    """Split cleaned text into short spoken chunks with natural boundaries."""
    cleaned = prepare_text_for_speech(text)
    if not cleaned:
        return []

    raw_parts = re.split(r"(?<=[.!?])\s+", cleaned)
    chunks: list[str] = []
    buf = ""

    for part in raw_parts:
        part = part.strip()
        if not part:
            continue
        candidate = f"{buf} {part}".strip() if buf else part
        if len(candidate) <= max_chunk:
            buf = candidate
            continue
        if buf:
            chunks.append(buf)
        if len(part) <= max_chunk:
            buf = part
        else:
            # Hard split very long sentences on commas.
            subs = re.split(r",\s+", part)
            sub_buf = ""
            for sub in subs:
                sub = sub.strip()
                if not sub:
                    continue
                cand = f"{sub_buf}, {sub}".strip(", ") if sub_buf else sub
                if len(cand) <= max_chunk:
                    sub_buf = cand
                else:
                    if sub_buf:
                        chunks.append(sub_buf)
                    sub_buf = sub
            if sub_buf:
                chunks.append(sub_buf)
            buf = ""

    if buf:
        chunks.append(buf)

    return [c.strip(" ,.;:!?") for c in chunks if c.strip()]
