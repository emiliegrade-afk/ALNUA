"""R&D Drill curriculum — NUAWAY Next (SPEC_STUDIO_ACADEMIES / DEC-036, Phase 49.4).

10 drill exercises N1→N3 for the R&D Lab (5 agents) : un dossier exploratoire
papier complet pour la prochaine brique de NUAWAY (écosystème vanlife/nomades).
Cadence hebdomadaire (items idle le lundi) — un dossier papier par semaine au
lieu du pipeline de production. Program config lives in
``academy_program_rnd.py``.

Side-effect discipline: the production R&D pipeline writes to Supabase
(repositories, dossiers tables). All 5 agents therefore train via the shared
AgentBase ``run_json_task`` path — same persona LLM capability, zero writes.
QA by rnd_committee (Cléo) via the engine's default DoD review.
"""

from __future__ import annotations

from services.studio_academy_program import StudioExercise

SUBJECT = "NUAWAY Next"
SLUG = "nuaway-next"
POLE = "innovation"

LEVEL_META: dict[int, dict[str, str | int]] = {
    1: {"name": "Exploration", "focus": "Concepts, faisabilité, plan, narratif, grille comité", "exercises": 5},
    2: {"name": "Approfondissement", "focus": "Variantes, risques, section marché", "exercises": 3},
    3: {"name": "Verdict", "focus": "Synthèse exécutive et verdict simulé du comité", "exercises": 2},
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
        _e("RD1.1", 1, "brainstorm", "run_json_task",
           "Idéation NUAWAY Next",
           "Génère 10 concepts de nouvelles briques pour NUAWAY Next (écosystème vanlife/nomades) : "
           "pour chacun, titre, problème résolu, cible, effort estimé (S/M/L). Vise l'utile "
           "quotidien d'un vanlifer, pas le gadget.",
           "ideation/concepts.md",
           dod=["10 concepts distincts", "Problème et cible par concept", "Effort estimé par concept"]),
        _e("RD1.2", 1, "rnd_agent", "run_json_task",
           "Faisabilité technique top 3",
           "Prends les 3 concepts les plus prometteurs du livrable d'idéation et analyse la "
           "faisabilité technique de chacun : stack, dépendances, points durs, time-to-MVP.",
           "faisabilite/top3.md",
           refs=["ideation/concepts.md"],
           dod=["3 concepts analysés", "Stack et dépendances par concept", "Time-to-MVP estimé"]),
        _e("RD1.3", 1, "rnd_dossier", "run_json_task",
           "Plan du dossier papier",
           "Structure le plan complet du dossier exploratoire NUAWAY Next : sections, contenu "
           "attendu par section, données nécessaires. Format dossier R&D ALNUA.",
           "dossier/plan.md",
           dod=["Au moins 6 sections", "Contenu attendu par section", "Données nécessaires identifiées"]),
        _e("RD1.4", 1, "rnd_ceo", "run_json_task",
           "Angle narratif CEO",
           "Formule l'angle narratif CEO de NUAWAY Next : pourquoi maintenant, pour qui, quelle "
           "ambition — en 1 paragraphe + 3 messages clés. Ton investisseur bienveillant mais exigeant.",
           "narratif/angle-ceo.md",
           dod=["Paragraphe d'ambition", "3 messages clés", "Réponse explicite à « pourquoi maintenant »"]),
        _e("RD1.5", 1, "rnd_committee", "run_json_task",
           "Grille d'évaluation comité",
           "Conçois la grille d'évaluation que le comité R&D appliquera aux concepts NUAWAY Next : "
           "critères pondérés, seuils de décision (GO/PIVOT/NO-GO), déroulé de séance de 30 minutes.",
           "comite/grille-evaluation.md",
           dod=["Au moins 5 critères pondérés", "Seuils GO/PIVOT/NO-GO définis", "Déroulé de séance décrit"]),
    ]


def _n2() -> list[StudioExercise]:
    return [
        _e("RD2.1", 2, "brainstorm", "run_json_task",
           "Variantes du concept retenu",
           "Le comité a retenu le concept le mieux noté. Décline-le en 3 variantes (minimaliste / "
           "standard / ambitieuse) avec périmètre, différenciation et premier utilisateur cible "
           "de chacune.",
           "ideation/variantes.md",
           refs=["ideation/concepts.md", "comite/grille-evaluation.md"],
           dod=["3 variantes distinctes", "Périmètre par variante", "Premier utilisateur cible identifié"]),
        _e("RD2.2", 2, "rnd_agent", "run_json_task",
           "Risques et dépendances",
           "Pour la variante standard, cartographie les risques techniques et les dépendances "
           "externes (APIs, données, hardware éventuel). Note probabilité/impact et propose une "
           "mitigation par risque majeur.",
           "faisabilite/risques.md",
           refs=["ideation/variantes.md"],
           dod=["Au moins 5 risques identifiés", "Probabilité et impact notés", "Mitigation par risque majeur"]),
        _e("RD2.3", 2, "rnd_dossier", "run_json_task",
           "Section marché",
           "Rédige la section marché du dossier NUAWAY Next : taille de la communauté "
           "vanlife/nomade adressable, segments, concurrents directs et indirects, fenêtre "
           "d'opportunité.",
           "dossier/section-marche.md",
           refs=["dossier/plan.md", "narratif/angle-ceo.md"],
           dod=["Marché quantifié (ordres de grandeur assumés)", "Segments définis", "Au moins 3 concurrents positionnés"]),
    ]


def _n3() -> list[StudioExercise]:
    return [
        _e("RD3.1", 3, "rnd_ceo", "run_json_task",
           "Synthèse exécutive",
           "Rédige la synthèse exécutive 1 page du dossier NUAWAY Next : concept retenu, marché, "
           "faisabilité, risques majeurs, demande (GO pour prototype papier). C'est la page "
           "qu'Emilie lit en premier.",
           "narratif/synthese-executive.md",
           refs=["dossier/section-marche.md", "faisabilite/risques.md"],
           dod=["Tient en 1 page", "Concept + marché + risques couverts", "Demande explicite (GO/attente)"]),
        _e("RD3.2", 3, "rnd_committee", "run_json_task",
           "Verdict simulé du comité",
           "Simule la séance du comité R&D sur NUAWAY Next : applique la grille d'évaluation à la "
           "synthèse exécutive, rends un verdict motivé (GO/PIVOT/NO-GO) et liste les conditions "
           "de la prochaine étape.",
           "comite/verdict.md",
           refs=["comite/grille-evaluation.md", "narratif/synthese-executive.md"],
           dod=["Grille appliquée critère par critère", "Verdict explicite et motivé", "Conditions de prochaine étape listées"]),
    ]


def all_exercises() -> list[StudioExercise]:
    return _n1() + _n2() + _n3()


def get_exercise(exercise_id: str) -> StudioExercise | None:
    return next((e for e in all_exercises() if e.exercise_id == exercise_id), None)
