"""Comms Academy curriculum — Lancement NAÏA (SPEC_STUDIO_ACADEMIES / DEC-036).

30 studio exercises N1→N4 for the Comms Hub (10 agents). Deliverables are the
complete paper campaign for the NAÏA wellness app launch — real product, so
training output becomes the actual launch canon. V1 = paper campaign only:
no posts queued, no campaigns created, no ad spend (production-side-effect
methods stay for real work — agents train via ``handle_instruction`` or the
shared AgentBase ``run_json_task`` path). Program config lives in
``academy_program_comms.py``.
"""

from __future__ import annotations

from services.studio_academy_program import StudioExercise

SUBJECT = "NAÏA"
SLUG = "naia-launch"
POLE = "comms"

LEVEL_META: dict[int, dict[str, str | int]] = {
    1: {"name": "Fondations solo", "focus": "Livrables de base par rôle", "exercises": 10},
    2: {"name": "Interdépendances", "focus": "Livrables croisés entre rôles", "exercises": 8},
    3: {"name": "Campagne complète", "focus": "Assemblage semaine de lancement", "exercises": 8},
    4: {"name": "Pré-production", "focus": "Package prêt pour activation réelle", "exercises": 4},
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
        _e("CN1.1", 1, "marketing", "handle_instruction",
           "Stratégie de lancement NAÏA",
           "Définis la stratégie de lancement de NAÏA, l'app wellness ALNUA (8 univers : féminin, "
           "sport, nutrition, quotidien, bien-être, nature, witchy, settings) : positionnement, "
           "audiences prioritaires, canaux, phasage pré-lancement / jour J / J+7.",
           "strategy/strategie-lancement.md",
           dod=["Positionnement explicite", "Au moins 3 audiences prioritaires", "Phasage en 3 temps"]),
        _e("CN1.2", 1, "content", "handle_instruction",
           "Piliers de contenu",
           "Définis les piliers de contenu de la campagne NAÏA : les grands thèmes récurrents qui "
           "porteront tous les posts, avec exemples par pilier et le ton NAÏA (bienveillant, "
           "concret, jamais culpabilisant).",
           "editorial/piliers-contenu.md",
           dod=["Au moins 4 piliers", "Exemples concrets par pilier", "Ton NAÏA explicité"]),
        _e("CN1.3", 1, "content_app", "run_json_task",
           "Calendrier éditorial — semaine de lancement",
           "Construis le calendrier éditorial de la semaine de lancement de NAÏA (J-1 à J+5) : "
           "posts par jour et par plateforme, formats variés. Ta spécialité : les calendriers "
           "éditoriaux app — applique-la à NAÏA.",
           "editorial/calendrier-lancement.md",
           dod=["7 jours couverts", "Au moins 2 posts par jour", "Formats variés (post, story, thread)"]),
        _e("CN1.4", 1, "content_gaming", "run_json_task",
           "Plan de teasers pré-lancement",
           "Conçois le plan de teasers pré-lancement de NAÏA : mécanique de montée en tension "
           "sur 2 semaines, sans tout révéler. Ta spécialité : les teasers et la hype — "
           "transpose-la du gaming au wellness.",
           "editorial/teasers-pre-lancement.md",
           dod=["Au moins 5 teasers ordonnés", "Arc de montée explicite", "Call-to-action par teaser"]),
        _e("CN1.5", 1, "content_robo", "run_json_task",
           "Plan build-in-public NAÏA",
           "Conçois le volet build-in-public du lancement NAÏA : raconter les coulisses de "
           "conception de l'app (jalons, défis, choix) pour créer une audience avant la sortie. "
           "Ta spécialité : le build-in-public — applique-la à une app wellness.",
           "editorial/build-in-public.md",
           dod=["Au moins 5 jalons narratifs", "Format de contenu par jalon", "Angle coulisses assumé"]),
        _e("CN1.6", 1, "content_company", "run_json_task",
           "Annonce corporate — lancement NAÏA",
           "Rédige l'annonce corporate du lancement de NAÏA (style communiqué) : ce que c'est, "
           "pour qui, pourquoi maintenant, par ALNUA. Voix de marque ALNUA.",
           "corporate/annonce-lancement.md",
           dod=["Structure d'annonce complète", "Voix de marque ALNUA respectée", "Au moins 300 mots"]),
        _e("CN1.7", 1, "brand", "run_json_task",
           "Spec du kit brand de lancement",
           "Rédige la spec du kit visuel de lancement NAÏA : palette, typographies, ton visuel, "
           "et ses déclinaisons par univers de l'app (8 univers). Document de direction "
           "artistique, pas d'assets.",
           "brand/kit-lancement-spec.md",
           dod=["Palette définie (codes couleur)", "Typographies choisies", "Déclinaison par univers NAÏA"]),
        _e("CN1.8", 1, "rnd_social", "run_json_task",
           "Stratégie social teasers — countdown",
           "Définis la stratégie de teasing social pour le countdown de lancement NAÏA : "
           "mécaniques par plateforme, rythme, jauge de mystère. Ta spécialité : les pipelines "
           "de teasers sociaux — applique-la au lancement.",
           "social/strategie-teasers.md",
           dod=["Calendrier de countdown", "Mécanique par plateforme", "Règles de révélation progressive"]),
        _e("CN1.9", 1, "rnd_visual", "design_visual_concept",
           "Moodboard & direction visuelle campagne",
           "Définis la direction visuelle de la campagne NAÏA : 3 territoires visuels explorés, "
           "cohérence avec les 8 univers de l'app, specs des assets clés à produire. Document "
           "de moodboard textuel, pas d'images.",
           "visual/direction-visuelle.md",
           kwargs={"concept_name": "Campagne lancement NAÏA", "constraints": "bienveillant, jamais culpabilisant ; déclinable sur 8 univers"},
           dod=["3 territoires visuels décrits", "Cohérence avec les 8 univers", "Specs des assets clés"]),
        _e("CN1.10", 1, "ads", "handle_instruction",
           "Plan média payant — stratégie d'acquisition",
           "Établis la stratégie d'acquisition payante du lancement NAÏA : plateformes, budgets "
           "phasés, objectifs par phase, KPIs. Document de planification — aucune campagne "
           "réelle à créer.",
           "ads/plan-media.md",
           dod=["Au moins 2 plateformes", "Budget phasé chiffré", "KPIs par phase"]),
    ]


def _n2() -> list[StudioExercise]:
    return [
        _e("CN2.1", 2, "content_app", "run_json_task",
           "Posts semaine 1 — univers Sport & Nutrition",
           "Rédige les posts de la semaine 1 pour les univers Sport et Nutrition de NAÏA, "
           "cohérents avec les piliers de contenu et le calendrier de lancement.",
           "editorial/posts-semaine1-sport-nutrition.md",
           refs=["editorial/piliers-contenu.md", "editorial/calendrier-lancement.md"],
           dod=["Au moins 6 posts rédigés", "Cohérents avec les piliers", "Déclinés sur 2 plateformes"]),
        _e("CN2.2", 2, "content_gaming", "run_json_task",
           "Séquence teaser J-7 → J-1",
           "Écris la séquence complète des teasers J-7 à J-1 du lancement NAÏA : un teaser par "
           "jour, montée narrative, cohérent avec la direction visuelle.",
           "editorial/sequence-teasers-j7.md",
           refs=["editorial/teasers-pre-lancement.md", "visual/direction-visuelle.md"],
           dod=["7 teasers datés", "Montée narrative lisible", "Cohérent avec la direction visuelle"]),
        _e("CN2.3", 2, "rnd_visual", "design_visual_concept",
           "Specs visuelles des teasers J-7",
           "Rédige les specs visuelles de chaque teaser de la séquence J-7 : composition, "
           "palette, format par plateforme, notes de production.",
           "visual/specs-teasers-j7.md",
           kwargs={"concept_name": "Teasers J-7 → J-1 du lancement NAÏA", "constraints": "une spec par teaser, formats stories + feed"},
           refs=["editorial/sequence-teasers-j7.md", "visual/direction-visuelle.md"],
           dod=["Une spec par teaser", "Formats par plateforme", "Notes de production actionnables"]),
        _e("CN2.4", 2, "content", "handle_instruction",
           "Kit de posts organiques — lancement",
           "Rédige le kit de posts organiques du jour J : annonce + posts de soutien, déclinés "
           "par plateforme, dans le respect du kit brand et des piliers.",
           "editorial/posts-organiques-lancement.md",
           refs=["editorial/piliers-contenu.md", "brand/kit-lancement-spec.md"],
           dod=["Au moins 8 posts rédigés", "Déclinaisons par plateforme", "Respect du kit brand"]),
        _e("CN2.5", 2, "rnd_social", "run_json_task",
           "Plan d'amplification communauté",
           "Conçois le plan d'amplification communauté du lancement NAÏA : mécaniques "
           "d'engagement (UGC, défis, partages), calendrier, règles de modération.",
           "social/plan-amplification.md",
           refs=["social/strategie-teasers.md"],
           dod=["Mécaniques d'engagement définies", "Calendrier d'animation", "Règles de modération"]),
        _e("CN2.6", 2, "ads", "handle_instruction",
           "Campagnes payantes — wave 1",
           "Structure les campagnes payantes de la wave 1 (pré-lancement) : objectif, audience, "
           "budget, variantes A/B par campagne, sur la base du plan média et des posts "
           "organiques. Document de structure — aucune campagne réelle à créer.",
           "ads/campagnes-wave1.md",
           refs=["ads/plan-media.md", "editorial/posts-organiques-lancement.md"],
           dod=["Au moins 3 campagnes structurées", "Variantes A/B définies", "KPIs par campagne"]),
        _e("CN2.7", 2, "brand", "run_json_task",
           "Review de cohérence — livrables N1/N2",
           "Relis les livrables produits jusqu'ici (kit brand, posts organiques, direction "
           "visuelle) : liste les écarts de cohérence de marque et propose les corrections. "
           "Ta spécialité : la cohérence brand — applique ta grille de review.",
           "brand/review-coherence-n2.md",
           refs=["brand/kit-lancement-spec.md", "editorial/posts-organiques-lancement.md", "visual/direction-visuelle.md"],
           dod=["Chaque livrable relu", "Écarts listés explicitement", "Corrections proposées"]),
        _e("CN2.8", 2, "content_company", "run_json_task",
           "FAQ presse & éléments de langage",
           "Rédige la FAQ presse du lancement NAÏA : questions probables des médias, réponses "
           "calibrées, éléments de langage ALNUA, cohérent avec l'annonce corporate.",
           "corporate/faq-presse.md",
           refs=["corporate/annonce-lancement.md", "strategy/strategie-lancement.md"],
           dod=["Au moins 8 questions/réponses", "Éléments de langage listés", "Cohérent avec l'annonce"]),
    ]


def _n3() -> list[StudioExercise]:
    return [
        _e("CN3.1", 3, "marketing", "handle_instruction",
           "Plan de lancement intégré — synthèse",
           "Assemble le plan de lancement intégré de NAÏA : synthèse de la stratégie, du plan "
           "média et du calendrier éditorial, timeline J-14 → J+14, budget global, responsables "
           "par volet.",
           "strategy/plan-integre.md",
           refs=["strategy/strategie-lancement.md", "ads/plan-media.md", "editorial/calendrier-lancement.md"],
           dod=["Tous les volets synthétisés", "Timeline J-14 → J+14", "Budget global chiffré"]),
        _e("CN3.2", 3, "content", "handle_instruction",
           "Kit contenu jour J",
           "Rédige le kit contenu complet du jour J : annonce principale, posts par plateforme, "
           "stories, prêt à publier, cohérent avec le plan intégré.",
           "editorial/kit-jour-j.md",
           refs=["editorial/piliers-contenu.md", "brand/kit-lancement-spec.md", "strategy/plan-integre.md"],
           dod=["Annonce + posts + stories", "Tous canaux couverts", "Prêt à publier tel quel"]),
        _e("CN3.3", 3, "content_app", "run_json_task",
           "Éditorial in-app & onboarding",
           "Rédige le volet éditorial in-app du lancement : messages d'accueil, onboarding par "
           "univers, notifications de la première semaine — cohérent avec la campagne.",
           "editorial/onboarding-editorial.md",
           refs=["editorial/piliers-contenu.md"],
           dod=["Au moins 5 écrans/messages rédigés", "Ton adapté par univers", "Cohérent avec la campagne"]),
        _e("CN3.4", 3, "content_robo", "run_json_task",
           "Récit build-in-public — semaine de lancement",
           "Écris le récit build-in-public de la semaine de lancement : un post de coulisses "
           "par jour (J-1 à J+5), vulnérabilité assumée, call-to-action téléchargement.",
           "editorial/bip-semaine-lancement.md",
           refs=["editorial/build-in-public.md", "strategy/plan-integre.md"],
           dod=["7 jours de récit rédigés", "Angle coulisses cohérent", "CTA téléchargement présent"]),
        _e("CN3.5", 3, "rnd_visual", "design_visual_concept",
           "Specs assets jour J",
           "Rédige les specs de production de tous les assets visuels du jour J : visuels "
           "d'annonce, templates stories, bannières store — formats, palettes, notes pour les "
           "designers.",
           "visual/specs-assets-jour-j.md",
           kwargs={"concept_name": "Assets visuels jour J — lancement NAÏA", "constraints": "couvrir annonce, stories, bannières store iOS/Android"},
           refs=["editorial/kit-jour-j.md", "visual/direction-visuelle.md"],
           dod=["Spec par asset", "Formats par plateforme et store", "Prêt pour production"]),
        _e("CN3.6", 3, "ads", "handle_instruction",
           "Campagnes jour J & règles d'optimisation",
           "Structure l'activation payante du jour J : campagnes activées, règles "
           "d'optimisation (enchères, rotation des créas, kill/scale), budget pacing sur 7 "
           "jours. Document d'ops — aucune campagne réelle à créer.",
           "ads/campagnes-jour-j.md",
           refs=["ads/campagnes-wave1.md", "strategy/plan-integre.md"],
           dod=["Plan d'activation jour J", "Règles d'optimisation explicites", "Budget pacing 7 jours"]),
        _e("CN3.7", 3, "brand", "run_json_task",
           "Kit brand final — validation",
           "Finalise le kit brand de lancement NAÏA : intègre les corrections de ta review de "
           "cohérence, complète les specs assets, livre le kit prêt pour les designers.",
           "brand/kit-final.md",
           refs=["brand/kit-lancement-spec.md", "brand/review-coherence-n2.md", "visual/specs-assets-jour-j.md"],
           dod=["Corrections N2 intégrées", "Kit complet (palette, typo, assets, ton)", "Prêt pour designers"]),
        _e("CN3.8", 3, "rnd_social", "run_json_task",
           "Plan social J+7 — rétention",
           "Conçois le plan social post-lancement (J+1 à J+7) : transformer l'attention du "
           "lancement en communauté durable — contenus, mécaniques de rétention, KPIs.",
           "social/plan-j7-retention.md",
           refs=["social/plan-amplification.md", "editorial/kit-jour-j.md"],
           dod=["Calendrier J+1 → J+7", "Mécaniques de rétention", "KPIs de communauté"]),
    ]


def _n4() -> list[StudioExercise]:
    return [
        _e("CN4.1", 4, "marketing", "handle_instruction",
           "Go/no-go & budget final",
           "Rédige la note de décision go/no-go du lancement NAÏA : critères mesurables, budget "
           "final validé, risques et plans B. Synthèse pour la direction ALNUA.",
           "strategy/go-no-go.md",
           refs=["strategy/plan-integre.md", "ads/campagnes-jour-j.md"],
           dod=["Critères mesurables", "Budget final validé", "Risques et plans B"]),
        _e("CN4.2", 4, "content_company", "run_json_task",
           "Kit presse final",
           "Assemble le kit presse final du lancement NAÏA : communiqué, FAQ, liste des visuels "
           "à joindre, contacts — prêt à envoyer aux médias.",
           "corporate/kit-presse.md",
           refs=["corporate/faq-presse.md", "corporate/annonce-lancement.md"],
           dod=["Communiqué + FAQ + visuels listés", "Prêt à envoyer", "Cohérent avec le kit brand"]),
        _e("CN4.3", 4, "ads", "handle_instruction",
           "Runbook ops publicité",
           "Rédige le runbook ops des campagnes payantes : procédures J-1 → J+7, alertes et "
           "seuils, escalade en cas de dérive de coûts. Document d'exploitation.",
           "ads/runbook-ops.md",
           refs=["ads/campagnes-jour-j.md"],
           dod=["Procédures J-1 → J+7", "Alertes et seuils chiffrés", "Procédure d'escalade"]),
        _e("CN4.4", 4, "brand", "run_json_task",
           "Critères d'acceptation campagne",
           "Définis les critères d'acceptation de la campagne NAÏA avant activation réelle : "
           "checklist qualité par livrable, seuils, décision explicite. Synthèse finale de "
           "l'académie comms.",
           "brand/criteres-acceptation.md",
           refs=["brand/kit-final.md", "strategy/plan-integre.md"],
           dod=["Checklist qualité par livrable", "Seuils explicites", "Décision go/no-go explicite"]),
    ]


def all_exercises() -> list[StudioExercise]:
    return [*_n1(), *_n2(), *_n3(), *_n4()]


def get_exercise(exercise_id: str) -> StudioExercise | None:
    for ex in all_exercises():
        if ex.exercise_id == exercise_id:
            return ex
    return None
