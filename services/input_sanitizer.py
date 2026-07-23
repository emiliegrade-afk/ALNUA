"""User input sanitization — prompt injection guard + length limits."""

from __future__ import annotations

import re
import unicodedata

# Patterns commonly used in prompt injection attempts
_INJECTION_PATTERNS: tuple[re.Pattern[str], ...] = tuple(
    re.compile(p, re.I)
    for p in (
        r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions",
        r"disregard\s+(your\s+)?(system|instructions)",
        r"you\s+are\s+now\s+(a\s+)?(?:DAN|jailbreak|unrestricted)",
        r"<\s*/?\s*system\s*>",
        r"```\s*system",
        r"override\s+(system|safety)\s+prompt",
        r"reveal\s+(your\s+)?(system\s+)?prompt",
        r"act\s+as\s+if\s+you\s+have\s+no\s+restrictions",
    )
)

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

# Basic PII patterns — redact before LLM
_PII_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"), "[email]"),
    (re.compile(r"\b(?:\+33|0)[1-9][\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}[\s.-]?\d{2}\b"), "[phone]"),
    (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "[card]"),
    (re.compile(r"\b\d{15,16}\b"), "[number]"),
)


def redact_pii(text: str) -> str:
    """Mask common PII patterns before sending to LLM."""
    result = text
    for pattern, replacement in _PII_PATTERNS:
        result = pattern.sub(replacement, result)
    return result


def sanitize_user_input(
    text: str,
    *,
    max_length: int = 4000,
    strip_injection: bool = True,
    redact_pii_enabled: bool = True,
) -> str:
    """
    Normalize and bound user text before LLM calls.
    Strips control chars, collapses whitespace, enforces max length.
    """
    if not text:
        return ""

    # NFC normalization — consistent unicode
    cleaned = unicodedata.normalize("NFC", text)
    cleaned = _CONTROL_CHARS.sub("", cleaned)
    cleaned = re.sub(r"\n{4,}", "\n\n\n", cleaned)
    cleaned = cleaned.strip()

    if strip_injection:
        for pattern in _INJECTION_PATTERNS:
            cleaned = pattern.sub("[filtered]", cleaned)

    if redact_pii_enabled:
        cleaned = redact_pii(cleaned)

    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rstrip() + "…"

    return cleaned


def estimate_tokens(text: str) -> int:
    """Rough token estimate (4 chars ≈ 1 token) for budget checks."""
    return max(1, len(text) // 4)
