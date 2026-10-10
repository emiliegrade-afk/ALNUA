"""Analytics Drill curriculum — Hub Autopsy (SPEC_STUDIO_ACADEMIES / DEC-036, Phase 49.4).

10 drill exercises N1→N3 for the Analytics Room (2 agents). Subject: the hub
itself — Layla and Axel learn their trade on ALNUA's own operation (agent
activity, LLM costs, idle queue, academies) so the output doubles as real
insight. Program config lives in ``academy_program_analytics.py``.

Method discipline: only prompt-interpolation-safe methods are used (str kwargs
rendered into f-strings). Methods joining list params (``funnel_analysis``,
``dashboard_spec``) are excluded — the engine passes str kwargs only.
"""

from __future__ import annotations

from services.studio_academy_program import StudioExercise

SUBJECT = "Hub ALNUA"
SLUG = "hub-autopsy"
POLE = "analytics"

LEVEL_META: dict[int, dict[str, str | int]] = {
    1: {"name": "Fondations métriques", "focus": "KPIs et requêtes de base sur le Hub", "exercises": 4},
    2: {"name": "Analyse des données", "focus": "Anomalies et recherche sur données réelles", "exercises": 4},
    3: {"name": "Synthèse décisionnelle", "focus": "Funnel idle et brief ROI pour Aria", "exercises": 2},
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
        _e("AN1.1", 1, "analyst_business", "define_kpis",
           "KPIs du Hub ALNUA",
           "Définis le système de KPIs du Hub ALNUA tel qu'il tourne aujourd'hui : plateforme "
           "multi-agents perso, 53 agents, coût LLM quotidien plafonné, académies en cours.",
           "kpis/kpis-hub.md",
           kwargs={"project": "Hub ALNUA — plateforme multi-agents", "stage": "beta",
                   "business_goal": "Maximiser le throughput d'agents utile par dollar LLM dépensé"},
           dod=["North star metric définie avec cible", "Au moins 4 KPIs primaires avec fréquence", "Au moins 2 anti-métriques identifiées"]),
        _e("AN1.2", 1, "analyst_data", "sql_query",
           "Taux de succès par agent (30 j)",
           "Écris la requête qui révèle quels agents du Hub réussissent le mieux — base du "
           "classement compétition.",
           "sql/success-rate-agents.md",
           kwargs={"question": "Quels agents ont le meilleur taux de succès sur les 30 derniers jours, et lesquels échouent le plus ?",
                   "schema_context": "table agent_logs: agent_id (text), action (text), status (text: success|error), created_at (timestamptz)"},
           dod=["Requête SQL PostgreSQL valide", "Explication en langage naturel", "Fenêtre 30 jours respectée"]),
        _e("AN1.3", 1, "analyst_business", "market_analysis",
           "Positionnement du Hub",
           "Analyse le marché dans lequel le Hub ALNUA se situe réellement — pas pour le vendre, "
           "mais pour calibrer les choix d'architecture face aux outils existants.",
           "marche/positionnement-hub.md",
           kwargs={"product": "Hub ALNUA (orchestration multi-agents LLM personnel)",
                   "market": "outils d'orchestration multi-agents LLM pour fondateurs solo"},
           dod=["TAM/SAM/SOM estimés", "Au moins 3 concurrents analysés", "Positionnement recommandé explicite"]),
        _e("AN1.4", 1, "analyst_data", "sql_query",
           "Coûts LLM par modèle",
           "Écris la requête de suivi des coûts LLM — le poste de dépense n°1 du Hub.",
           "sql/couts-par-modele.md",
           kwargs={"question": "Quel est le coût LLM par modèle et par agent sur 30 jours, et quel modèle domine la dépense ?",
                   "schema_context": "table cost_log: agent_id (text), model (text), prompt_tokens (int), completion_tokens (int), cost_usd (numeric), created_at (timestamptz)"},
           dod=["Requête SQL PostgreSQL valide", "Agrégation par modèle ET par agent", "Explication en langage naturel"]),
    ]


def _n2() -> list[StudioExercise]:
    return [
        _e("AN2.1", 2, "analyst_data", "anomaly_report",
           "Anomalie coût LLM quotidien",
           "La dépense LLM quotidienne grimpe depuis que les académies tournent (6 exercices/jour). "
           "Analyse cette série et dis si c'est une dérive ou la nouvelle normale.",
           "anomalies/cout-llm-j7.md",
           kwargs={"metric": "daily_llm_cost_usd", "recent_values": "[1.8, 2.1, 2.0, 2.4, 3.1, 4.2, 5.6]",
                   "baseline": "2.0", "period": "7 jours"},
           refs=["sql/couts-par-modele.md"],
           dod=["Direction et déviation chiffrées", "Sévérité justifiée", "Au moins 2 causes plausibles identifiées", "Actions recommandées"]),
        _e("AN2.2", 2, "analyst_business", "user_research",
           "Workflows dépendants du Hub",
           "Conçois la recherche qui identifie quels workflows quotidiens d'Emilie dépendent le "
           "plus du Hub — et lesquels souffrent quand le Hub est éteint.",
           "research/workflows-dependants.md",
           kwargs={"product": "Hub ALNUA",
                   "research_question": "Quels workflows quotidiens d'Emilie dépendent le plus du Hub, et que se passe-t-il quand il est éteint ?",
                   "user_segment": "Emilie — fondatrice solo, usage quotidien"},
           dod=["Méthodologie choisie et justifiée", "Au moins 5 questions d'interview", "Hypothèses à valider listées"]),
        _e("AN2.3", 2, "analyst_data", "anomaly_report",
           "Taux de succès académies",
           "Le taux de succès quotidien des académies fluctue fortement. Analyse la série et "
           "recommande les métriques de suivi à mettre en place.",
           "anomalies/success-academies-j7.md",
           kwargs={"metric": "academy_daily_success_rate_pct", "recent_values": "[100, 100, 75, 100, 50, 100, 66]",
                   "baseline": "90", "period": "7 jours"},
           refs=["kpis/kpis-hub.md"],
           dod=["Anomalie détectée ou absence justifiée", "Sévérité notée", "Métriques de suivi proposées"]),
        _e("AN2.4", 2, "analyst_business", "define_kpis",
           "KPIs Studio Academies",
           "Définis les KPIs propres aux académies (gaming, robo, comms, drills) : progression, "
           "qualité QA, coût par exercice validé.",
           "kpis/kpis-academies.md",
           kwargs={"project": "Studio Academies (gaming, robo, comms, drills)", "stage": "launch",
                   "business_goal": "Former 30 agents sur projets papier sans risque production, avec progression mesurable"},
           refs=["kpis/kpis-hub.md"],
           dod=["North star propre aux académies", "KPIs couvrant progression ET qualité QA", "Anti-métriques identifiées"]),
    ]


def _n3() -> list[StudioExercise]:
    return [
        _e("AN3.1", 3, "analyst_data", "sql_query",
           "Funnel idle queue par famille",
           "Écris la requête qui mesure le funnel de la file idle du jour : quel pourcentage "
           "d'items est réellement exécuté avant minuit, par famille.",
           "sql/funnel-idle-familles.md",
           kwargs={"question": "Quel pourcentage d'items idle du jour sont exécutés avant minuit, par famille (gaming, robo, comms, ops, self_dev) ?",
                   "schema_context": "table idle_items: id (text), kind (text), family (text), status (text), queue_date (date), finished_at (timestamptz)"},
           refs=["sql/success-rate-agents.md", "sql/couts-par-modele.md"],
           dod=["Requête SQL PostgreSQL valide", "Regroupement par famille", "Taux calculé en pourcentage"]),
        _e("AN3.2", 3, "analyst_business", "strategic_brief",
           "Brief ROI pour Aria",
           "Rédige le brief stratégique de synthèse pour Aria (COO) : le Hub vaut-il son coût "
           "de fonctionnement, et faut-il ajuster budget ou cadence ?",
           "briefs/brief-roi-hub.md",
           kwargs={"topic": "ROI du fonctionnement du Hub et des académies",
                   "context": "Académies en cours (gaming, robo, comms, drills), budget LLM 10 USD/j, drains idle toutes les 3 h.",
                   "decision_needed": "Faut-il augmenter le budget LLM quotidien (10 USD/j) ou réallouer les drains idle ?"},
           refs=["anomalies/cout-llm-j7.md", "anomalies/success-academies-j7.md", "sql/funnel-idle-familles.md"],
           dod=["Executive summary de 3 phrases maximum", "Au moins 2 options avec pros/cons", "Recommandation explicite"]),
    ]


def all_exercises() -> list[StudioExercise]:
    return _n1() + _n2() + _n3()


def get_exercise(exercise_id: str) -> StudioExercise | None:
    return next((e for e in all_exercises() if e.exercise_id == exercise_id), None)
