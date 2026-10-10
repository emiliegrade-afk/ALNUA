"""Finance Drill curriculum — Budgets Projets Papier (SPEC_STUDIO_ACADEMIES / DEC-036, Phase 49.4).

10 drill exercises N1→N3 for the Accounting Office (2 agents). Jules and Rémi
build the budgets of the hub's own paper projects (Eve robot, NAÏA launch) —
the numbers that will matter when the academies ship. Program config lives in
``academy_program_finance.py``.

Side-effect discipline: all methods used are read-only (financial_advice,
analyze_costs, build_forecast, monthly_report compute from kwargs + read-only
spend/invoice snapshots; list_open_invoices only reads). No ledger writes.

Kwarg order matters: the engine appends cross-deliverable context to the LAST
declared kwarg — keep it a free-text param (question, budget, assumptions,
all_data). ``list_open_invoices`` takes no refs for that reason.
"""

from __future__ import annotations

from services.studio_academy_program import StudioExercise

SUBJECT = "Eve + NAÏA"
SLUG = "paper-budgets"
POLE = "finance"

LEVEL_META: dict[int, dict[str, str | int]] = {
    1: {"name": "État des lieux", "focus": "Trésorerie et coûts des projets papier", "exercises": 4},
    2: {"name": "Projections", "focus": "Forecasts Eve et NAÏA", "exercises": 4},
    3: {"name": "Arbitrage", "focus": "Rapport mensuel et séquence d'investissement", "exercises": 2},
}


def _e(
    eid: str,
    level: int,
    agent: str,
    method: str,
    title: str,
    brief: str,
    path: str,
    *,
    kwargs: dict[str, str] | None = None,
    refs: list[str] | None = None,
    dod: list[str],
) -> StudioExercise:
    return StudioExercise(eid, level, agent, method, title, brief, path, kwargs or {}, refs or [], dod)


def _n1() -> list[StudioExercise]:
    return [
        _e("FN1.1", 1, "accounting", "financial_advice",
           "Trésorerie T4 2026",
           "Évalue la capacité d'absorption de la trésorerie ALNUA pour le trimestre : les deux "
           "projets papier (Eve, NAÏA) ont des budgets à engager, les revenus sont nuls.",
           "treso/treso-2026-10.md",
           kwargs={"month": "2026-10",
                   "financial_summary": "Revenus: 0 EUR. Coûts LLM: ~60 USD/mois. SaaS/outils: ~120 USD/mois. Pas de salaires.",
                   "question": "Peut-on absorber le BOM papier d'Eve (~450 EUR) et le budget lancement NAÏA (~1200 EUR) ce trimestre sans risque de trésorerie ?"},
           dod=["Synthèse de 2-3 phrases", "Alertes explicites si budget non absorbable", "Une prochaine étape unique"]),
        _e("FN1.2", 1, "controller", "analyze_costs",
           "Coûts lancement NAÏA",
           "Analyse la structure de coûts du lancement NAÏA prévu en novembre et compare au "
           "budget alloué.",
           "couts/lancement-naia-q4.md",
           kwargs={"period": "2026-Q4",
                   "costs_data": "Publicité: 800 EUR. Assets/créas: 200 EUR. Outils: 60 EUR/mois.",
                   "budget": "Lancement NAÏA: 1200 EUR"},
           dod=["Statut vs budget explicite (under/on_track/over)", "Top cost drivers listés", "Au moins 1 recommandation actionnable"]),
        _e("FN1.3", 1, "accounting", "financial_advice",
           "Hygiène factures",
           "Le suivi des factures est manuel et sporadique. Recommande une hygiène de suivi "
           "adaptée à une fondatrice solo.",
           "treso/hygiene-factures.md",
           kwargs={"month": "2026-10",
                   "financial_summary": "Factures fournisseurs sporadiques (SaaS, matériel). Suivi manuel, aucune échéance manquée à ce jour.",
                   "question": "Quelles habitudes de suivi des factures mettre en place pour ne plus jamais payer en retard sans y passer ses soirées ?"},
           dod=["Recommandations concrètes", "Prochaine étape unique", "Mention de la politique de paiement"]),
        _e("FN1.4", 1, "controller", "analyze_costs",
           "BOM Eve v0",
           "Recalcule et challenge le BOM papier du prototype Eve v0 issu de la Robo Academy.",
           "couts/bom-eve-v0.md",
           kwargs={"period": "2026-10",
                   "costs_data": "BOM Eve estimé: Pi 5 90 EUR, servos x6 120 EUR, capteurs 60 EUR, chassis impression 3D 45 EUR, batterie 40 EUR, divers 50 EUR",
                   "budget": "Eve v0 prototype: 450 EUR"},
           dod=["Total recalculé et comparé au budget", "Variance en pourcentage", "Alertes si dépassement"]),
    ]


def _n2() -> list[StudioExercise]:
    return [
        _e("FN2.1", 2, "controller", "build_forecast",
           "Forecast Eve 12 mois",
           "Construis le forecast financier 12 mois du projet Eve, du prototype papier aux "
           "unités pilotes.",
           "forecasts/eve-12m.md",
           kwargs={"project": "Eve — compagnon de bureau", "horizon_months": "12",
                   "assumptions": "Prototype v0 en 2027-Q1 (~450 EUR BOM). 10 unités pilotes en 2027-Q3. Prix cible 399 EUR. Marge brute cible 45 %."},
           refs=["couts/bom-eve-v0.md"],
           dod=["Forecast mensuel sur 12 mois", "Break-even identifié ou absence justifiée", "Investissement total chiffré", "Hypothèses clés listées"]),
        _e("FN2.2", 2, "accounting", "financial_advice",
           "Plafond récurrent SaaS + LLM",
           "Fixe le plafond de dépenses récurrentes tant que les revenus sont nuls.",
           "treso/plafond-recurrent.md",
           kwargs={"month": "2026-10",
                   "financial_summary": "LLM ~60 USD/mois, SaaS ~120 USD/mois, revenus 0 EUR. Budget idle quotidien 10 USD/j.",
                   "question": "Quel plafond mensuel SaaS+LLM recommandes-tu tant que les revenus sont nuls, et quels postes couper en priorité si dépassement ?"},
           refs=["treso/treso-2026-10.md"],
           dod=["Plafond chiffré proposé", "Ordre de coupe priorisé", "Prochaine étape unique"]),
        _e("FN2.3", 2, "controller", "build_forecast",
           "Forecast NAÏA 6 mois",
           "Construis le forecast financier 6 mois du lancement NAÏA.",
           "forecasts/naia-6m.md",
           kwargs={"project": "NAÏA — compagnon bien-être", "horizon_months": "6",
                   "assumptions": "Lancement 2026-11. 500 téléchargements M1, croissance 30 %/mois. Conversion premium 4 %. Abonnement 6,99 EUR/mois. Coût ads 800 EUR M1 puis 400 EUR/mois."},
           refs=["couts/lancement-naia-q4.md"],
           dod=["Forecast mensuel sur 6 mois", "Revenue mensuel chiffré", "Break-even ou trajectoire explicite", "Risques listés"]),
        _e("FN2.4", 2, "accounting", "list_open_invoices",
           "État des factures ouvertes",
           "Dresse l'état réel des factures ouvertes suivies par le Hub et synthétise le total "
           "à payer — c'est le seul exercice du drill sur données de production (lecture seule).",
           "treso/factures-ouvertes.md",
           kwargs={"status": "to_pay"},
           dod=["Factures listées avec montants", "Synthèse du total à payer"]),
    ]


def _n3() -> list[StudioExercise]:
    return [
        _e("FN3.1", 3, "controller", "monthly_report",
           "Rapport mensuel papier 2026-10",
           "Génère le rapport financier mensuel d'octobre en intégrant les forecasts Eve et "
           "NAÏA produits par le drill.",
           "reports/rapport-2026-10.md",
           kwargs={"month": "2026-10",
                   "all_data": "Revenus: 0 EUR. Coûts: LLM 60 USD, SaaS 120 USD, BOM Eve 405 EUR engagés sur papier, budget NAÏA 1200 EUR provisionné. Forecasts Eve et NAÏA disponibles dans le workspace."},
           refs=["forecasts/eve-12m.md", "forecasts/naia-6m.md"],
           dod=["Executive summary pour Aria", "Revenue/costs/net structurés", "Au moins 1 highlight et 1 concern", "Outlook mois suivant"]),
        _e("FN3.2", 3, "accounting", "financial_advice",
           "Séquence d'investissement 2027",
           "Recommande la séquence d'investissement 2027 entre les trois chantiers (Eve, NAÏA, "
           "Hub) à partir des forecasts du drill.",
           "reco/sequence-investissement-2027.md",
           kwargs={"month": "2026-10",
                   "financial_summary": "Forecasts Eve (12 mois) et NAÏA (6 mois) validés sur papier. Trésorerie limitée, revenus nuls.",
                   "question": "Quelle séquence d'investissement 2027 recommandes-tu entre Eve, NAÏA et le Hub, et à quels signaux conditionner chaque étape ?"},
           refs=["forecasts/eve-12m.md", "forecasts/naia-6m.md", "treso/plafond-recurrent.md"],
           dod=["Séquence ordonnée explicite", "Signaux/conditions par étape", "Prochaine étape unique"]),
    ]


def all_exercises() -> list[StudioExercise]:
    return _n1() + _n2() + _n3()


def get_exercise(exercise_id: str) -> StudioExercise | None:
    return next((e for e in all_exercises() if e.exercise_id == exercise_id), None)
