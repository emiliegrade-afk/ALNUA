"""COO / Telegram — natural-language pattern matching for ideas and R&D."""

from __future__ import annotations

import re


IDEA_CAPTURE_PREFIXES = (
    "note cette idée",
    "note l'idée",
    "note l idee",
    "note cette idee",
    "boîte à idées",
    "boite a idees",
    "boîte a idees",
    "garde cette idée",
    "garde cette idee",
    "idée en vrac",
    "idee en vrac",
    "idée:",
    "idee:",
    "#idee",
    "#idée",
)

IDEA_CAPTURE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^j['']?ai une idée(?: pour)?\s*[:.]?\s*(.+)$", re.I | re.S),
    re.compile(r"^nouvelle idée\s*[:.]?\s*(.+)$", re.I | re.S),
    re.compile(r"^explore l['']idée (?:de |d[''])?(.+)$", re.I | re.S),
    re.compile(r"^idée r&d\s*[:.]?\s*(.+)$", re.I | re.S),
)

INVESTIGATION_MARKERS = (
    "recherche r&d",
    "recherche rnd",
    "lance une recherche r&d",
    "lance une recherche rnd",
    "investiguer",
    "investigue",
    "investigation",
    "demande au r&d",
    "demande au rnd",
    "demande à r&d",
    "demande a r&d",
    "le r&d doit",
    "le rnd doit",
    "alex doit",
    "rnd doit",
    "r&d doit",
    "analyse le marché",
    "analyse la tendance",
    "analyse les tendances",
    "faisabilité",
    "faisabilite",
    "retour sur investissement",
    "roi ",
    " rentabilité",
    "rentabilite",
)

INVESTIGATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(?:demande(?:r)?\s+(?:au\s+)?r&?d\s+(?:d['']?)?(?:investiguer|analyser|regarder|étudier|etudier)\s+(?:sur\s+)?)(.+)$",
        re.I | re.S,
    ),
    re.compile(
        r"(?:r&?d\s+(?:doit|peut)\s+(?:investiguer|analyser|regarder)\s+(?:sur\s+)?)(.+)$",
        re.I | re.S,
    ),
    re.compile(
        r"(?:investiguer|investigue|analyser|analyse|étudier|etudier)\s+(?:sur\s+)?(?:le\s+|la\s+|les\s+|l[''])?(.+)$",
        re.I | re.S,
    ),
    re.compile(r"(?:tendance|trending)\s*[:.]?\s*(.+)$", re.I | re.S),
    re.compile(
        r"(?:quel(?:le)?s?\s+)?(?:est\s+)?(?:la\s+)?faisabilit[eé]\s+(?:du |de la |de l['']|des )?(.+?)(?:\?|$)",
        re.I | re.S,
    ),
    re.compile(
        r"(?:retour sur investissement|roi)\s+(?:du |de la |de l['']|pour )?(.+?)(?:\?|$)",
        re.I | re.S,
    ),
    re.compile(
        r"(?:lance(?:r)?\s+(?:une\s+)?)?recherche(?:r)?\s+(?:pour\s+)?(?:r&?d|rnd)\s*[:.]?\s*(.+)$",
        re.I | re.S,
    ),
)


def clean_extracted(text: str) -> str:
    cleaned = text.strip().strip("«»\"'.,;:!?")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned


def extract_idea_text(instruction: str) -> str | None:
    """Extract idea body from a natural-language capture message."""
    raw = instruction.strip()
    if not raw:
        return None

    lower = raw.lower()
    for prefix in IDEA_CAPTURE_PREFIXES:
        if lower.startswith(prefix):
            body = raw[len(prefix) :].strip(" :.-")
            return clean_extracted(body) if body else None

    for pattern in IDEA_CAPTURE_PATTERNS:
        match = pattern.match(raw)
        if match:
            body = clean_extracted(match.group(1))
            if body:
                return body

    return None


def detect_idea_capture(instruction: str) -> bool:
    """True when the message should be saved to the R&D idea inbox."""
    if extract_idea_text(instruction):
        return True
    lower = instruction.lower().strip()
    return any(lower.startswith(p) for p in IDEA_CAPTURE_PREFIXES)


def extract_investigation_query(instruction: str) -> str | None:
    """Extract research topic from an R&D investigation request."""
    raw = instruction.strip()
    if not raw:
        return None

    lower = raw.lower()
    if not any(marker in lower for marker in INVESTIGATION_MARKERS):
        if not re.search(r"\b(r&?d|rnd)\b", lower, re.I):
            return None
        if not re.search(r"\b(investig|analys|trend|tendance|marché|marche|étud|etud)\b", lower, re.I):
            return None

    for pattern in INVESTIGATION_PATTERNS:
        match = pattern.search(raw)
        if match:
            topic = clean_extracted(match.group(1))
            if len(topic) >= 4:
                return topic

    fallback = re.sub(
        r"^(?:demande(?:r)?\s+(?:au\s+)?r&?d\s+(?:d['']?)?(?:investiguer|analyser)\s+(?:sur\s+)?)",
        "",
        raw,
        flags=re.I,
    ).strip()
    fallback = clean_extracted(fallback)
    if len(fallback) >= 4 and fallback.lower() != lower:
        return fallback

    return None


def detect_rnd_investigation(instruction: str) -> bool:
    return extract_investigation_query(instruction) is not None
