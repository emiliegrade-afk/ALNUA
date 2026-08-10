"""Finance estimate constants — effort, domain, and cost model defaults."""
from __future__ import annotations

import os

# Effort → agent work duration (weeks of solo+AI pipeline, not human payroll)
EFFORT_WEEKS: dict[str, int] = {
    "S": 2,
    "M": 4,
    "L": 10,
    "XL": 20,
}

DOMAIN_MULTIPLIER: dict[str, float] = {
    "app": 1.0,
    "saas": 1.15,
    "ia": 1.1,
    "jeu": 1.3,
    "game": 1.3,
    "gaming": 1.3,
    "hardware": 1.6,
    "robotique": 1.6,
    "robotics": 1.6,
    "autre": 1.0,
}

DOMAIN_REVENUE_POTENTIAL: dict[str, float] = {
    "app": 1.2,
    "saas": 1.5,
    "ia": 1.3,
    "jeu": 0.85,
    "game": 0.85,
    "gaming": 0.85,
    "hardware": 0.55,
    "robotique": 0.55,
    "robotics": 0.55,
    "autre": 1.0,
}

EFFORT_REVENUE_SPEED: dict[str, float] = {
    "S": 1.25,
    "M": 1.0,
    "L": 0.75,
    "XL": 0.55,
}

COST_MODEL = os.getenv("RND_COST_MODEL", "ai_solo").lower()
FINANCE_VERSION = 3

LLM_EUR_PER_AGENT_WEEK = float(os.getenv("RND_LLM_EUR_PER_AGENT_WEEK", "14"))
DOSSIER_ENRICH_EUR = float(os.getenv("RND_DOSSIER_ENRICH_EUR", "8"))
MARKETING_LAUNCH_EUR = float(os.getenv("RND_MARKETING_LAUNCH_EUR", "80"))
PROJECT_HOSTING_MONTHLY_EUR = float(os.getenv("RND_PROJECT_HOSTING_MONTHLY_EUR", "12"))

HOURLY_RATE_EUR = float(os.getenv("RND_DEV_HOURLY_RATE_EUR", "50"))
HOURS_PER_WEEK = int(os.getenv("RND_DEV_HOURS_PER_WEEK", "20"))
BASE_OPEX_MONTHLY = float(os.getenv("RND_BASE_OPEX_MONTHLY_EUR", "45"))
LEGACY_LLM_MONTHLY_EUR = float(os.getenv("RND_LLM_MONTHLY_EUR", "30"))
