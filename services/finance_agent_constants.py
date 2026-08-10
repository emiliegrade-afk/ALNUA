"""Finance agent — category constants and LLM system prompt."""

from __future__ import annotations

FINANCE_MODEL = "anthropic/claude-3-haiku"

EXPENSE_CATEGORIES = (
    "saas_tools",
    "hardware",
    "freelance",
    "marketing",
    "legal",
    "hosting",
    "formation",
    "autre",
)

INCOME_CATEGORIES = (
    "app_revenue",
    "grant",
    "consulting",
    "investment",
    "autre",
)

CATEGORY_LABELS: dict[str, str] = {
    "saas_tools": "Outils SaaS",
    "hardware": "Matériel",
    "freelance": "Freelance",
    "marketing": "Marketing",
    "legal": "Juridique",
    "hosting": "Hébergement",
    "formation": "Formation",
    "autre": "Autre",
    "app_revenue": "Revenus app",
    "grant": "Subvention",
    "consulting": "Consulting",
    "investment": "Investissement",
}

SYSTEM_PROMPT = (
    "Tu es l'agent comptable d'Emilie, fondatrice d'ALNUA. "
    "Tu génères des résumés mensuels financiers clairs, directs et positifs. "
    "Tu signales les anomalies (dépense inhabituelle, baisse de revenu) sans dramatiser."
)
