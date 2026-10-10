"""Gaming Academy curriculum — Wyrdheim Paper Slice (SPEC_GAMING_ACADEMY / DEC-034).

30 studio exercises N1→N4, deliverable-based: each produces a markdown document
in the write-only workspace. V1 = paper slice, no UE dependency. Program config
for the generic engine lives in ``academy_program_gaming.py`` (DEC-036).
"""

from __future__ import annotations

from services.studio_academy_program import StudioExercise

GAME = "Wyrdheim"
SLUG = "gaming-academy"
POLE = "gaming"

LEVEL_META: dict[int, dict[str, str | int]] = {
    1: {"name": "Fondations solo", "focus": "Livrables de base par rôle", "exercises": 10},
    2: {"name": "Interdépendances", "focus": "Livrables croisés entre rôles", "exercises": 8},
    3: {"name": "Vertical slice papier", "focus": "Assemblage zone tutoriel", "exercises": 8},
    4: {"name": "Pré-production", "focus": "Package prêt pour UE5.8", "exercises": 4},
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
        _e("GN1.1", 1, "game_director", "handle_instruction",
           "Vision & pillars — zone tutoriel",
           "Définis la vision créative de la zone tutoriel « Clairière de Départ » : 3 pillars "
           "de game design, le ton (fantasy nordique), l'expérience visée pour un joueur "
           "découvrant Wyrdheim, et les contraintes de scope d'un tutoriel (15-20 min).",
           "direction/vision-zone-tutoriel.md",
           dod=["3 pillars explicites", "Ton fantasy nordique affirmé", "Contraintes de scope tutoriel listées"]),
        _e("GN1.2", 1, "narrative_designer", "write_dialogue",
           "PNJ mentor — dialogues d'accueil",
           "Écris les dialogues d'accueil de Brynja, la mentor de la zone tutoriel.",
           "narrative/pnj-mentor-dialogues.md",
           kwargs={"npc_name": "Brynja la Mentor", "context": "PNJ mentor de la zone tutoriel, accueille le joueur", "tone": "chaleureux et sage"},
           dod=["Au moins 3 répliques", "Voix de mentor crédible", "Cohérent fantasy nordique"]),
        _e("GN1.3", 1, "level_designer", "design_quest",
           "Quête tutoriel « Premiers Pas »",
           "Conçois la quête principale du tutoriel : le joueur apprend déplacement, interaction et combat de base.",
           "quests/quete-tutoriel-01.md",
           kwargs={"quest_name": "Premiers Pas", "quest_type": "main", "player_level_range": "1-3"},
           dod=["Au moins 3 objectifs", "Récompenses définies", "Durée estimée ≤ 20 min"]),
        _e("GN1.4", 1, "environment_artist", "design_environment",
           "Biome de la Clairière de Départ",
           "Conçois l'habillage visuel de la zone tutoriel : props, végétation, architecture, palette.",
           "environnement/biome-tutoriel.md",
           kwargs={"zone_name": "Clairière de Départ", "biome": "forêt boréale", "mood": "éveil mystique"},
           dod=["Props listés", "Palette de couleurs définie", "Au moins 2 points d'intérêt"]),
        _e("GN1.5", 1, "technical_artist", "run_studio_task",
           "Conventions assets & budgets",
           "Rédige les conventions de nommage des assets, les budgets perf cibles (polygones, "
           "textures, draw calls) et les formats d'export pour le studio.",
           "tech-art/conventions-assets.md",
           dod=["Convention de nommage explicite", "Budgets perf chiffrés", "Formats d'export listés"]),
        _e("GN1.6", 1, "vfx_artist", "design_vfx",
           "VFX signature — runes de guidage",
           "Conçois l'effet des runes de guidage qui orientent le joueur dans le tutoriel.",
           "vfx/vfx-signature.md",
           kwargs={"effect_name": "Runes de guidage", "trigger": "progression tutoriel", "style": "magie nordique discrète"},
           dod=["Déclencheur défini", "Style visuel décrit", "Budget perf mentionné"]),
        _e("GN1.7", 1, "sound_designer", "design_soundscape",
           "Soundscape de la Clairière",
           "Conçois l'ambiance sonore de la zone tutoriel : nappes, SFX clés, transitions.",
           "audio/soundscape-tutoriel.md",
           kwargs={"scene_name": "Clairière de Départ", "mood": "calme éveil", "key_sfx": "vent, oiseaux, murmure de runes"},
           dod=["Nappes d'ambiance décrites", "Au moins 3 SFX clés", "Transitions indiquées"]),
        _e("GN1.8", 1, "ai_programmer", "design_behavior",
           "Behavior du PNJ mentor",
           "Conçois l'arbre de comportement de Brynja : accueil, attente, guidage du joueur.",
           "ai/behavior-pnj-mentor.md",
           kwargs={"entity_name": "Brynja la Mentor", "behavior_type": "friendly_npc", "difficulty": "easy"},
           dod=["Arbre de comportement structuré", "États d'attente/accueil/guidage", "Transitions explicites"]),
        _e("GN1.9", 1, "dev_gaming", "handle_instruction",
           "Spec architecture — module quêtes",
           "Rédige la spec technique du système de quêtes (C++ UE5) : classes, responsabilités, "
           "dépendances, points d'extension. Document de conception, pas de code.",
           "dev/spec-module-quetes.md",
           dod=["Classes C++ listées", "Responsabilités par classe", "Dépendances identifiées"]),
        _e("GN1.10", 1, "qa_gaming", "build_test_plan",
           "Plan de test — zone tutoriel",
           "Construis le plan de test de la zone tutoriel (paper slice) : scénarios critiques "
           "de première expérience joueur.",
           "qa/test-plan-zone-tutoriel.md",
           kwargs={"feature_name": "Zone tutoriel — paper slice", "risk_areas": "première expérience joueur, lisibilité du guidage"},
           dod=["Au moins 5 cas de test", "Priorités assignées", "Critères de sortie définis"]),
    ]


def _n2() -> list[StudioExercise]:
    return [
        _e("GN2.1", 2, "level_designer", "design_quest",
           "Quête secondaire « Le Chêne Blessé »",
           "Conçois une quête secondaire confiée par Brynja : purifier le Chêne Ancien. "
           "Réutilise le PNJ mentor et fais suite à « Premiers Pas ».",
           "quests/quete-tutoriel-02.md",
           kwargs={"quest_name": "Le Chêne Blessé", "quest_type": "side", "player_level_range": "2-4"},
           refs=["narrative/pnj-mentor-dialogues.md", "quests/quete-tutoriel-01.md"],
           dod=["Référence Brynja (PNJ existant)", "Suite logique de Premiers Pas", "Au moins 3 objectifs"]),
        _e("GN2.2", 2, "narrative_designer", "write_dialogue",
           "Dialogues de « Le Chêne Blessé »",
           "Écris les dialogues de Brynja pour la quête Le Chêne Blessé (début, progression, fin).",
           "narrative/dialogues-quete-02.md",
           kwargs={"npc_name": "Brynja la Mentor", "context": "Quête Le Chêne Blessé : purification du Chêne Ancien", "tone": "inquiet mais confiant"},
           refs=["quests/quete-tutoriel-02.md"],
           dod=["Dialogues pour les 3 temps de la quête", "Cohérent avec les dialogues d'accueil"]),
        _e("GN2.3", 2, "level_designer", "write_lore_entry",
           "Lore — Le Chêne Ancien",
           "Écris l'entrée codex du Chêne Ancien, cohérente avec le biome de la Clairière.",
           "narrative/lore-chene-ancien.md",
           kwargs={"subject": "Le Chêne Ancien", "lore_type": "place", "length": "medium"},
           refs=["environnement/biome-tutoriel.md"],
           dod=["Longueur 250-350 mots", "Cohérent avec le biome", "Au moins 2 entrées liées proposées"]),
        _e("GN2.4", 2, "environment_artist", "design_environment",
           "Sous-zone — Sentier du Chêne",
           "Décline le biome en sous-zone : le sentier menant au Chêne Ancien, progression visuelle "
           "de la corruption vers l'arbre.",
           "environnement/sentier-chene.md",
           kwargs={"zone_name": "Sentier du Chêne", "biome": "forêt boréale corrompue", "mood": "déclin progressif"},
           refs=["environnement/biome-tutoriel.md", "narrative/lore-chene-ancien.md"],
           dod=["Cohérent avec le biome parent", "Progression visuelle de la corruption décrite"]),
        _e("GN2.5", 2, "sound_designer", "design_soundscape",
           "Soundscape combat tutoriel",
           "Conçois l'ambiance sonore du combat d'apprentissage de « Premiers Pas » : montée de "
           "tension, SFX de combat léger, résolution.",
           "audio/soundscape-combat.md",
           kwargs={"scene_name": "Combat tutoriel", "mood": "tension maîtrisée", "key_sfx": "épée, parade, souffle du joueur"},
           refs=["quests/quete-tutoriel-01.md"],
           dod=["Arc de tension décrit", "SFX de combat listés", "Cohérent avec le soundscape d'ambiance"]),
        _e("GN2.6", 2, "ai_programmer", "design_behavior",
           "Behavior — Sanglier des racines",
           "Conçois le comportement du sanglier des racines, ennemi du combat tutoriel : patrouille, "
           "charge, fuite à bas PV.",
           "ai/behavior-sanglier.md",
           kwargs={"entity_name": "Sanglier des racines", "behavior_type": "hostile", "difficulty": "easy"},
           refs=["environnement/biome-tutoriel.md"],
           dod=["Pattern lisible par un débutant", "Au moins 3 états", "Condition de fuite définie"]),
        _e("GN2.7", 2, "technical_artist", "optimize_render_budget",
           "Budget perf — Clairière de Départ",
           "Analyse le budget de rendu de la Clairière : props du biome + VFX des runes. Propose "
           "les optimisations pour tenir 60 FPS sur PC cible.",
           "tech-art/budget-perf-clairiere.md",
           kwargs={"scene_name": "Clairière de Départ", "target_fps": "60", "current_issues": "densité végétation + VFX runes"},
           refs=["environnement/biome-tutoriel.md", "vfx/vfx-signature.md", "tech-art/conventions-assets.md"],
           dod=["Budgets chiffrés par catégorie", "Au moins 3 optimisations proposées", "Respecte les conventions assets"]),
        _e("GN2.8", 2, "qa_gaming", "build_test_plan",
           "Plan de test — interdépendances N2",
           "Plan de test croisé : vérifier la cohérence quête/dialogues/lore du Chêne Blessé et "
           "le combat tutoriel.",
           "qa/test-plan-n2.md",
           kwargs={"feature_name": "Quêtes N2 et interdépendances", "risk_areas": "cohérence canon entre livrables"},
           refs=["quests/quete-tutoriel-02.md", "narrative/dialogues-quete-02.md"],
           dod=["Cas de test de cohérence croisée", "Au moins 5 cas", "Priorités assignées"]),
    ]


def _n3() -> list[StudioExercise]:
    return [
        _e("GN3.1", 3, "game_director", "handle_instruction",
           "GDD extract — zone tutoriel",
           "Rédige l'extrait GDD de la zone tutoriel : vision, contenu complet (quêtes, PNJ, "
           "ennemis, zones), progression joueur, critères d'expérience. Synthétise les livrables N1-N2.",
           "direction/gdd-extract-zone-tutoriel.md",
           refs=["direction/vision-zone-tutoriel.md", "quests/quete-tutoriel-01.md", "quests/quete-tutoriel-02.md"],
           dod=["Tout le contenu N1-N2 référencé", "Progression joueur décrite", "Aucun élément hors scope"]),
        _e("GN3.2", 3, "level_designer", "design_level",
           "Level design — zone tutoriel complète",
           "Conçois le flow complet de la zone : de l'arrivée au Chêne Ancien, zones, rencontres, "
           "checkpoints, secrets.",
           "quests/level-zone-tutoriel.md",
           kwargs={"level_name": "Clairière de Départ — zone complète", "biome": "forêt boréale", "difficulty": "easy"},
           refs=["environnement/biome-tutoriel.md", "environnement/sentier-chene.md", "quests/quete-tutoriel-02.md"],
           dod=["Flow zoné complet", "Rencontres clés positionnées", "Checkpoints définis"]),
        _e("GN3.3", 3, "narrative_designer", "write_dialogue",
           "Script cinématique d'intro",
           "Écris le script de la cinématique d'introduction : arrivée du joueur, première "
           "rencontre avec Brynja, accroche du Chêne Blessé.",
           "narrative/cinematique-intro.md",
           kwargs={"npc_name": "Brynja la Mentor", "context": "Cinématique d'introduction de la zone tutoriel", "tone": "solennel puis chaleureux"},
           refs=["direction/vision-zone-tutoriel.md", "narrative/pnj-mentor-dialogues.md"],
           dod=["Découpage en plans/scènes", "Dialogues intégrés", "Durée ≤ 90 secondes"]),
        _e("GN3.4", 3, "dev_gaming", "handle_instruction",
           "Spec technique — système de dialogues",
           "Rédige la spec technique du système de dialogues (C++ UE5) : données, déclencheurs, "
           "intégration cinématique d'intro. Document de conception, pas de code.",
           "dev/spec-systeme-dialogues.md",
           refs=["narrative/dialogues-quete-02.md", "narrative/cinematique-intro.md", "dev/spec-module-quetes.md"],
           dod=["Format de données défini", "Déclencheurs listés", "Cohérent avec la spec quêtes"]),
        _e("GN3.5", 3, "ai_programmer", "design_behavior",
           "Behavior — Gardien du Chêne (boss)",
           "Conçois le behavior du boss de fin de zone : le Gardien du Chêne corrompu, 2 phases.",
           "ai/behavior-boss-gardien.md",
           kwargs={"entity_name": "Gardien du Chêne", "behavior_type": "boss", "difficulty": "medium"},
           refs=["quests/level-zone-tutoriel.md", "narrative/lore-chene-ancien.md"],
           dod=["2 phases distinctes", "Tells lisibles avant chaque attaque", "Lien avec le lore du Chêne"]),
        _e("GN3.6", 3, "vfx_artist", "design_vfx",
           "VFX boss — phases du Gardien",
           "Conçois les effets des 2 phases du Gardien : corruption (phase 1) puis purification "
           "(phase 2).",
           "vfx/vfx-boss-gardien.md",
           kwargs={"effect_name": "Phases du Gardien du Chêne", "trigger": "transitions et attaques du boss", "style": "corruption puis lumière"},
           refs=["ai/behavior-boss-gardien.md"],
           dod=["Un effet par phase minimum", "Transition de phase lisible", "Cohérent avec les runes de guidage"]),
        _e("GN3.7", 3, "sound_designer", "design_soundscape",
           "Soundscape boss — Gardien du Chêne",
           "Conçois l'ambiance du combat de boss : thème musical, SFX des phases, stinger de victoire.",
           "audio/soundscape-boss.md",
           kwargs={"scene_name": "Boss Gardien du Chêne", "mood": "épique contenu", "key_sfx": "racines, corruption, purification"},
           refs=["ai/behavior-boss-gardien.md", "audio/soundscape-combat.md"],
           dod=["Thème par phase", "Stinger de victoire défini", "Transition musicale phase 1→2"]),
        _e("GN3.8", 3, "qa_gaming", "build_test_plan",
           "Plan de test — vertical slice",
           "Plan de test complet de la vertical slice papier : parcours joueur de bout en bout, "
           "boss, cinématique, cohérence canon.",
           "qa/test-plan-vertical-slice.md",
           kwargs={"feature_name": "Vertical slice zone tutoriel", "risk_areas": "boss 2 phases, cinématique intro, cohérence canon"},
           refs=["quests/level-zone-tutoriel.md", "ai/behavior-boss-gardien.md", "narrative/cinematique-intro.md"],
           dod=["Parcours bout en bout couvert", "Cas boss par phase", "Critères de sortie mesurables"]),
    ]


def _n4() -> list[StudioExercise]:
    return [
        _e("GN4.1", 4, "technical_artist", "run_studio_task",
           "Pipeline d'import UE5.8",
           "Rédige le pipeline d'import des assets dans UE5.8 : arborescence Content, règles LOD, "
           "naming appliqué, validation à l'import.",
           "tech-art/pipeline-import-ue.md",
           refs=["tech-art/conventions-assets.md", "tech-art/budget-perf-clairiere.md"],
           dod=["Arborescence Content définie", "Règles LOD explicites", "Checklist de validation import"]),
        _e("GN4.2", 4, "dev_gaming", "handle_instruction",
           "Plan d'implémentation C++ — ordre de build",
           "Rédige le plan d'implémentation du slice : ordre des modules (quêtes, dialogues, IA, "
           "boss), dépendances, jalons. Document de planification, pas de code.",
           "dev/plan-implementation-cpp.md",
           refs=["dev/spec-module-quetes.md", "dev/spec-systeme-dialogues.md", "direction/gdd-extract-zone-tutoriel.md"],
           dod=["Modules ordonnés avec dépendances", "Jalons mesurables", "Risques techniques identifiés"]),
        _e("GN4.3", 4, "game_director", "handle_instruction",
           "Critères d'acceptation production",
           "Définis les critères d'acceptation de la zone tutoriel pour passer en production UE : "
           "expérience joueur, contenu, perf, QA. Synthèse finale du paper slice.",
           "direction/criteres-acceptation.md",
           refs=["direction/gdd-extract-zone-tutoriel.md", "qa/test-plan-vertical-slice.md"],
           dod=["Critères mesurables", "Seuils QA référencés", "Décision go/no-go explicite"]),
        _e("GN4.4", 4, "qa_gaming", "build_test_plan",
           "Stratégie de validation pré-UE",
           "Définis la stratégie de validation avant bascule UE : ce qui est testé sur papier, ce "
           "qui le sera en moteur, critères de sortie du paper slice.",
           "qa/strategie-validation-pre-ue.md",
           kwargs={"feature_name": "Bascule paper slice → UE5.8", "risk_areas": "écarts papier/moteur, dette de test"},
           refs=["qa/test-plan-vertical-slice.md", "direction/criteres-acceptation.md"],
           dod=["Séparation papier/moteur explicite", "Critères de sortie du slice", "Dette de test listée"]),
    ]


def all_exercises() -> list[StudioExercise]:
    return [*_n1(), *_n2(), *_n3(), *_n4()]


def get_exercise(exercise_id: str) -> StudioExercise | None:
    for ex in all_exercises():
        if ex.exercise_id == exercise_id:
            return ex
    return None
