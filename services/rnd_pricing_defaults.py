"""R&D pricing — domain defaults and regex helpers."""

from __future__ import annotations

import re
from typing import Any

DOMAIN_TIER_DEFAULTS: dict[str, list[dict[str, Any]]] = {
    "saas": [
        {"name": "Starter", "price_eur": 16.99, "mix_pct": 0.42},
        {"name": "Pro", "price_eur": 49.0, "mix_pct": 0.32},
        {"name": "Studio", "price_eur": 99.0, "mix_pct": 0.18},
        {"name": "Business", "price_eur": 199.0, "mix_pct": 0.08},
    ],
    "ia": [
        {"name": "Solo", "price_eur": 19.0, "mix_pct": 0.45},
        {"name": "Pro", "price_eur": 59.0, "mix_pct": 0.35},
        {"name": "Team", "price_eur": 149.0, "mix_pct": 0.20},
    ],
    "app": [
        {"name": "Mensuel", "price_eur": 6.99, "mix_pct": 0.50},
        {"name": "Annuel", "price_eur": 49.0, "mix_pct": 0.35, "billing": "yearly"},
        {"name": "Premium", "price_eur": 14.99, "mix_pct": 0.15},
    ],
    "jeu": [
        {"name": "Base", "price_eur": 9.99, "mix_pct": 0.55, "billing": "one_time"},
        {"name": "Deluxe", "price_eur": 24.99, "mix_pct": 0.30, "billing": "one_time"},
        {"name": "Season pass", "price_eur": 12.99, "mix_pct": 0.15},
    ],
    "game": [
        {"name": "Base", "price_eur": 9.99, "mix_pct": 0.55, "billing": "one_time"},
        {"name": "Deluxe", "price_eur": 24.99, "mix_pct": 0.30, "billing": "one_time"},
        {"name": "Season pass", "price_eur": 12.99, "mix_pct": 0.15},
    ],
    "gaming": [
        {"name": "Base", "price_eur": 9.99, "mix_pct": 0.55, "billing": "one_time"},
        {"name": "Deluxe", "price_eur": 24.99, "mix_pct": 0.30, "billing": "one_time"},
        {"name": "Season pass", "price_eur": 12.99, "mix_pct": 0.15},
    ],
    "hardware": [
        {"name": "Kit standard", "price_eur": 89.0, "mix_pct": 0.65, "billing": "one_time"},
        {"name": "Kit pro", "price_eur": 149.0, "mix_pct": 0.25, "billing": "one_time"},
        {"name": "Abonnement cloud", "price_eur": 9.99, "mix_pct": 0.10},
    ],
    "autre": [
        {"name": "Essentiel", "price_eur": 14.99, "mix_pct": 0.50},
        {"name": "Pro", "price_eur": 39.0, "mix_pct": 0.35},
        {"name": "Premium", "price_eur": 79.0, "mix_pct": 0.15},
    ],
}

BASE_PAYING_SUBSCRIBERS: dict[str, dict[str, int]] = {
    "saas": {"m3": 10, "m6": 28, "m12": 62},
    "ia": {"m3": 8, "m6": 22, "m12": 50},
    "app": {"m3": 18, "m6": 45, "m12": 95},
    "jeu": {"m3": 120, "m6": 350, "m12": 800},
    "game": {"m3": 120, "m6": 350, "m12": 800},
    "gaming": {"m3": 120, "m6": 350, "m12": 800},
    "hardware": {"m3": 6, "m6": 18, "m12": 40},
    "autre": {"m3": 10, "m6": 25, "m12": 55},
}

EFFORT_M3_SCALE: dict[str, float] = {"S": 1.25, "M": 1.0, "L": 0.82, "XL": 0.65}
EFFORT_M12_SCALE: dict[str, float] = {"S": 0.55, "M": 1.0, "L": 1.35, "XL": 1.75}

PRICE_RE = re.compile(
    r"(?:€|EUR|\$|USD)\s*(\d+(?:[.,]\d{1,2})?)|(\d+(?:[.,]\d{1,2})?)\s*(?:€|EUR|\$|USD)",
    re.IGNORECASE,
)
RANGE_RE = re.compile(
    r"(\d+(?:[.,]\d{1,2})?)\s*[-–]\s*(\d+(?:[.,]\d{1,2})?)\s*(?:€|\$|EUR|USD|/mois|/month)",
    re.IGNORECASE,
)
TIER_LINE_RE = re.compile(
    r"(?i)(starter|solo|pro|studio|business|premium|team|essentiel|mensuel|annuel)\s*[|:]\s*"
    r"(\d+(?:[.,]\d{1,2})?)\s*€?",
)


def parse_price(raw: str) -> float:
    return float(raw.replace(",", "."))
