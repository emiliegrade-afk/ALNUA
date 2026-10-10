"""Robo Academy curriculum — Eve Paper Build (SPEC_STUDIO_ACADEMIES / DEC-036).

30 studio exercises N1→N4 for the Hardware Workshop (10 agents). Deliverables
are pre-production specs of Eve, the ALNUA desk companion robot — the real
product, so training output becomes production canon. V1 = paper build only,
no lab dependency. Program config lives in ``academy_program_robo.py``.
"""

from __future__ import annotations

from services.studio_academy_program import StudioExercise

SUBJECT = "Eve"
SLUG = "eve-paper-build"
POLE = "hardware"

LEVEL_META: dict[int, dict[str, str | int]] = {
    1: {"name": "Fondations solo", "focus": "Specs de base par rôle", "exercises": 10},
    2: {"name": "Interdépendances", "focus": "Specs croisées entre sous-systèmes", "exercises": 8},
    3: {"name": "Prototype papier", "focus": "Assemblage des sous-systèmes", "exercises": 8},
    4: {"name": "Pré-production", "focus": "Package prêt pour le lab Eve", "exercises": 4},
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
        _e("RN1.1", 1, "industrial_design", "design_form_factor",
           "Eve — identité produit compagnon de bureau",
           "Définis l'identité produit d'Eve, le robot compagnon de bureau ALNUA : form factor, "
           "dimensions cibles, matériaux, finitions, ergonomie d'un objet posé sur un bureau "
           "8h/jour. Ton : chaleureux, discret, premium accessible.",
           "design/identite-produit.md",
           kwargs={"product_name": "Eve — compagnon de bureau", "brand_notes": "ALNUA : chaleureux, discret, premium accessible"},
           dod=["Form factor défini avec dimensions cibles", "Matériaux et finitions listés", "Contraintes d'usage bureau identifiées"]),
        _e("RN1.2", 1, "mechanical", "design_part",
           "Châssis principal",
           "Conçois le châssis principal d'Eve : structure porteuse pour l'électronique, la tête "
           "articulée et la batterie, adapté à une vie sur bureau.",
           "meca/chassis-principal.md",
           kwargs={"part_name": "Châssis principal Eve", "function": "structure porteuse (électronique, tête articulée, batterie)", "load_requirements": "usage bureau : charges statiques, micro-vibrations, chute 80 cm"},
           dod=["Tolérances chiffrées", "Points de fixation listés", "Contraintes structurelles chiffrées"]),
        _e("RN1.3", 1, "electronics", "design_circuit",
           "Carte mère — architecture",
           "Conçois l'architecture de la carte mère d'Eve : distribution d'alimentation, hub "
           "capteurs, interface avec le Pi de contrôle.",
           "elec/carte-mere.md",
           kwargs={"circuit_name": "Carte mère Eve v1", "function": "distribution alim, hub capteurs, interface Pi", "constraints": "batterie 7.4V, budget 15W, encombrement chassis"},
           dod=["Blocs fonctionnels listés", "Protections identifiées", "Budget alimentation chiffré"]),
        _e("RN1.4", 1, "firmware", "design_driver",
           "Driver moteur de tête",
           "Conçois le driver firmware bas niveau des servos de tête (pan/tilt) d'Eve.",
           "firmware/driver-moteur-tete.md",
           kwargs={"component_name": "Servos tête (pan/tilt)", "timing_requirement": "boucle de contrôle 50 Hz", "constraints": "bus I2C partagé, watchdog obligatoire"},
           dod=["Interface du driver définie", "Timing chiffré", "Gestion d'erreurs décrite"]),
        _e("RN1.5", 1, "embedded_dev", "handle_instruction",
           "Spec application embarquée — machine d'états",
           "Rédige la spec de l'application embarquée d'Eve : machine d'états principale (veille, "
           "interaction, charge, alerte), transitions, comportement watchdog. Document de "
           "conception, pas de code.",
           "embedded/spec-app-embarquee.md",
           dod=["États listés et définis", "Transitions explicites", "Comportement watchdog décrit"]),
        _e("RN1.6", 1, "vision_ai", "design_detection_pipeline",
           "Détection de présence",
           "Conçois le pipeline de détection de présence d'Eve : repérer qu'un utilisateur est "
           "devant le robot, sur Pi, sans cloud.",
           "vision/detection-presence.md",
           kwargs={"task_name": "Détection de présence utilisateur", "target_objects": "visage, silhouette assise", "constraints": "Pi 5, caméra grand angle, latence < 500 ms"},
           dod=["Pipeline étape par étape", "Contraintes Pi respectées", "Latence cible chiffrée"]),
        _e("RN1.7", 1, "simulation", "run_simulation_plan",
           "Plan de simulation du châssis",
           "Construis le plan de simulation numérique du châssis et de la tête articulée avant "
           "tout prototypage physique.",
           "sim/plan-chassis.md",
           kwargs={"subsystem_name": "Châssis et tête articulée", "scenario": "mouvements pan/tilt répétés, stabilité sur bureau", "constraints": "pas de prototype physique à ce stade"},
           dod=["Scénarios listés", "Métriques mesurables", "Critères de réussite définis"]),
        _e("RN1.8", 1, "safety", "assess_risk",
           "Analyse de risques bureau",
           "Analyse les risques de sécurité d'Eve comme objet de bureau domestique : utilisateurs "
           "non avertis, enfants possibles, animaux.",
           "safety/risques-bureau.md",
           kwargs={"subsystem_name": "Eve compagnon de bureau (ensemble)", "hazard_type": "usage bureau domestique", "context": "utilisateurs non avertis, enfants possibles, animaux domestiques"},
           dod=["Au moins 5 risques identifiés", "Mitigation par risque", "Sévérité et probabilité notées"]),
        _e("RN1.9", 1, "hardware", "handle_instruction",
           "Sélection composants clés — BOM v0",
           "Établis la BOM v0 d'Eve : composants clés (calcul, servos, capteurs, batterie, écran) "
           "avec références, prix unitaires et disponibilité. Document de sourcing, pas d'achat.",
           "hardware/bom-v0.md",
           dod=["Composants chiffrés (référence + prix)", "Coût total estimé", "Disponibilité vérifiée"]),
        _e("RN1.10", 1, "qa_robot", "build_test_protocol",
           "Protocole de test du compagnon",
           "Construis le protocole de test hardware global d'Eve à ce stade papier : ce qu'il "
           "faudra vérifier sur le prototype, par fonction.",
           "qa/protocole-compagnon.md",
           kwargs={"subsystem_name": "Eve compagnon — ensemble", "risk_level": "medium", "prior_issues": "aucun retour terrain (pré-prototype)"},
           dod=["Au moins 5 protocoles de test", "Critères mesurables", "Priorités assignées"]),
    ]


def _n2() -> list[StudioExercise]:
    return [
        _e("RN2.1", 2, "mechanical", "design_part",
           "Support de tête articulée",
           "Conçois le support de tête articulée : interface entre le chassis principal et les "
           "servos pan/tilt.",
           "meca/support-tete.md",
           kwargs={"part_name": "Support de tête articulée", "function": "interface chassis ↔ servos pan/tilt", "load_requirements": "couple servo, 10k cycles"},
           refs=["meca/chassis-principal.md"],
           dod=["Compatible avec le chassis principal", "Tolérances chiffrées", "Interface servos définie"]),
        _e("RN2.2", 2, "electronics", "design_circuit",
           "Alimentation & charge batterie",
           "Conçois le circuit d'alimentation et de charge de la batterie d'Eve, cohérent avec "
           "la carte mère et la BOM v0.",
           "elec/alim-charge.md",
           kwargs={"circuit_name": "Alimentation & charge batterie", "function": "charge 2S, distribution protégée", "constraints": "batterie 7.4V 3000mAh, USB-C PD"},
           refs=["elec/carte-mere.md", "hardware/bom-v0.md"],
           dod=["Schéma de charge décrit", "Protections listées", "Cohérent avec la carte mère"]),
        _e("RN2.3", 2, "firmware", "design_driver",
           "Driver capteur de présence",
           "Conçois le driver firmware du capteur de présence choisi par le pipeline vision.",
           "firmware/driver-capteur-presence.md",
           kwargs={"component_name": "Capteur de présence (ToF/PIR selon vision)", "timing_requirement": "échantillonnage 10 Hz", "constraints": "bus I2C partagé avec les servos"},
           refs=["vision/detection-presence.md"],
           dod=["Interface définie", "Cohérent avec le pipeline vision", "Gestion d'erreurs décrite"]),
        _e("RN2.4", 2, "vision_ai", "design_detection_pipeline",
           "Reconnaissance du propriétaire",
           "Conçois le pipeline de reconnaissance du propriétaire (vs inconnu), on-device "
           "uniquement, respectueux de la vie privée.",
           "vision/reco-proprietaire.md",
           kwargs={"task_name": "Reconnaissance du propriétaire", "target_objects": "visage propriétaire vs inconnu", "constraints": "on-device, pas de cloud, vie privée"},
           refs=["vision/detection-presence.md"],
           dod=["Pipeline 100% on-device", "Gestion vie privée explicite", "Taux d'erreur cible chiffré"]),
        _e("RN2.5", 2, "safety", "assess_risk",
           "Risques batterie & charge",
           "Analyse les risques thermiques et électriques de la batterie et de la charge, en "
           "cohérence avec le circuit d'alimentation.",
           "safety/risques-batterie.md",
           kwargs={"subsystem_name": "Batterie & charge", "hazard_type": "thermique/électrique", "context": "charge USB-C sans surveillance, bureau en bois"},
           refs=["elec/alim-charge.md"],
           dod=["Risques thermiques couverts", "Mitigations matérielles ET logicielles", "Lien avec le circuit de charge"]),
        _e("RN2.6", 2, "simulation", "run_simulation_plan",
           "Simulation thermique",
           "Planifie la simulation thermique du chassis fermé en fonctionnement continu, sans "
           "ventilateur (silence bureau).",
           "sim/plan-thermique.md",
           kwargs={"subsystem_name": "Thermique du chassis fermé", "scenario": "charge + vision active en continu 8h", "constraints": "pas de ventilateur (silence bureau)"},
           refs=["meca/chassis-principal.md", "elec/carte-mere.md"],
           dod=["Scénario 8h continu", "Seuils de température chiffrés", "Recommandations design"]),
        _e("RN2.7", 2, "industrial_design", "design_form_factor",
           "Déclinaisons de finition",
           "Décline l'identité produit en 3 finitions compatibles avec le chassis : bureau sobre, "
           "maison chaleureuse, setup gaming.",
           "design/finitions.md",
           kwargs={"product_name": "Eve — déclinaisons de finition", "constraints": "reprendre le chassis principal tel quel", "brand_notes": "3 finitions : bureau sobre / maison chaleureuse / setup gaming"},
           refs=["design/identite-produit.md", "meca/chassis-principal.md"],
           dod=["3 finitions décrites", "Compatibilité chassis vérifiée", "Impact coût estimé"]),
        _e("RN2.8", 2, "qa_robot", "build_test_protocol",
           "Protocole batterie & thermique",
           "Construis le protocole de test batterie/charge/thermique : le sous-système au risque "
           "le plus élevé du produit.",
           "qa/protocole-batterie-thermique.md",
           kwargs={"subsystem_name": "Batterie, charge & thermique", "risk_level": "high", "prior_issues": "risques identifiés dans safety/risques-batterie.md"},
           refs=["elec/alim-charge.md", "sim/plan-thermique.md"],
           dod=["Protocoles charge/décharge définis", "Seuils thermiques mesurables", "Critères d'arrêt d'urgence"]),
    ]


def _n3() -> list[StudioExercise]:
    return [
        _e("RN3.1", 3, "hardware", "handle_instruction",
           "BOM v1 consolidé",
           "Consolide la BOM v1 d'Eve à partir de la v0 et des sous-systèmes conçus : chaque "
           "composant tracé à un sous-système, coût total resserré, alternatives pour les "
           "composants critiques.",
           "hardware/bom-v1.md",
           refs=["hardware/bom-v0.md", "elec/alim-charge.md", "elec/carte-mere.md"],
           dod=["Chaque composant tracé à un sous-système", "Coût total à ±10%", "Alternatives pour les 5 composants critiques"]),
        _e("RN3.2", 3, "mechanical", "design_part",
           "Ensemble tête articulée complet",
           "Conçois l'ensemble tête articulée complet : support, servos pan/tilt, logement de "
           "l'écran d'expression, pièce par pièce.",
           "meca/ensemble-tete.md",
           kwargs={"part_name": "Ensemble tête articulée complet", "function": "pan/tilt + support écran d'expression", "load_requirements": "10k cycles, jeu < 0.5°"},
           refs=["meca/support-tete.md", "firmware/driver-moteur-tete.md"],
           dod=["Assemblage décrit pièce par pièce", "Jeux et tolérances chiffrés", "Interface driver respectée"]),
        _e("RN3.3", 3, "embedded_dev", "handle_instruction",
           "Intégration vision ↔ machine d'états",
           "Rédige la spec d'intégration entre les pipelines vision et la machine d'états "
           "embarquée : quels événements vision déclenchent quelles transitions, latence "
           "bout-en-bout, modes dégradés. Document de conception, pas de code.",
           "embedded/integration-vision-etats.md",
           refs=["embedded/spec-app-embarquee.md", "vision/detection-presence.md", "vision/reco-proprietaire.md"],
           dod=["Événements vision → transitions tracés", "Latence bout-en-bout estimée", "Modes dégradés définis"]),
        _e("RN3.4", 3, "electronics", "design_circuit",
           "Carte capteurs",
           "Conçois la carte capteurs d'Eve (présence, IMU, micro) : acquisition et "
           "prétraitement, interface avec la carte mère.",
           "elec/carte-capteurs.md",
           kwargs={"circuit_name": "Carte capteurs (présence, IMU, micro)", "function": "acquisition + prétraitement", "constraints": "nappes courtes, CEM bureau"},
           refs=["elec/carte-mere.md", "firmware/driver-capteur-presence.md"],
           dod=["Liste des capteurs chiffrée", "Interface carte mère définie", "Contraintes CEM adressées"]),
        _e("RN3.5", 3, "firmware", "design_driver",
           "Driver écran d'expression",
           "Conçois le driver firmware de l'écran d'expression (yeux OLED) : interface "
           "d'animations, formats d'assets, cohérent avec l'identité produit.",
           "firmware/driver-ecran-expression.md",
           kwargs={"component_name": "Écran d'expression (yeux OLED)", "timing_requirement": "rafraîchissement 30 Hz animations", "constraints": "SPI partagé, budget RAM firmware"},
           refs=["design/identite-produit.md"],
           dod=["Interface animations définie", "Formats d'assets décrits", "Cohérent avec l'identité produit"]),
        _e("RN3.6", 3, "safety", "assess_risk",
           "Dossier de sécurité v1",
           "Consolide toutes les analyses de risques précédentes en un dossier de sécurité "
           "unique : matrice sévérité × probabilité, plan de mitigation global.",
           "safety/dossier-securite-v1.md",
           kwargs={"subsystem_name": "Eve — dossier de sécurité complet", "hazard_type": "tous", "context": "consolide les analyses précédentes en dossier unique"},
           refs=["safety/risques-bureau.md", "safety/risques-batterie.md", "sim/plan-chassis.md"],
           dod=["Analyses précédentes consolidées", "Matrice sévérité × probabilité", "Plan de mitigation global"]),
        _e("RN3.7", 3, "simulation", "run_simulation_plan",
           "Simulation de chute bureau",
           "Planifie la simulation de chute depuis un bureau (80 cm) : identifier les points de "
           "rupture probables avant le prototype.",
           "sim/plan-chute.md",
           kwargs={"subsystem_name": "Chute depuis un bureau (80 cm)", "scenario": "impact sur coin, tête articulée en position haute", "constraints": "identifier les points de rupture probables"},
           refs=["meca/chassis-principal.md", "safety/dossier-securite-v1.md"],
           dod=["Scénarios d'impact listés", "Points de rupture identifiés", "Recommandations de renforcement"]),
        _e("RN3.8", 3, "qa_robot", "build_test_protocol",
           "Protocole d'intégration prototype",
           "Construis le protocole d'intégration du prototype : séquence de bring-up ordonnée, "
           "test par sous-système, critères de passage globaux.",
           "qa/protocole-integration.md",
           kwargs={"subsystem_name": "Prototype Eve — intégration complète", "risk_level": "high", "prior_issues": "points de rupture de la simulation de chute"},
           refs=["meca/ensemble-tete.md", "embedded/integration-vision-etats.md", "elec/carte-capteurs.md"],
           dod=["Séquence de bring-up ordonnée", "Test par sous-système", "Critères de passage globaux"]),
    ]


def _n4() -> list[StudioExercise]:
    return [
        _e("RN4.1", 4, "hardware", "handle_instruction",
           "Plan de sourcing & commandes",
           "Établis le plan de sourcing du prototype Eve : fournisseurs par composant critique, "
           "délais estimés, budget total de la commande prototype, à partir de la BOM v1.",
           "hardware/plan-sourcing.md",
           refs=["hardware/bom-v1.md"],
           dod=["Fournisseurs par composant critique", "Délais estimés", "Budget total commande prototype"]),
        _e("RN4.2", 4, "embedded_dev", "handle_instruction",
           "Plan de bring-up — premier allumage",
           "Rédige le plan de bring-up du prototype : étapes ordonnées du premier allumage, "
           "points de mesure à chaque étape, critères go/no-go. Document de procédure.",
           "embedded/plan-bringup.md",
           refs=["embedded/spec-app-embarquee.md", "qa/protocole-integration.md"],
           dod=["Étapes ordonnées du premier allumage", "Points de mesure listés", "Critères go/no-go par étape"]),
        _e("RN4.3", 4, "safety", "assess_risk",
           "Checklist conformité pré-prototype",
           "Établis la checklist de conformité pré-prototype : normes applicables (marché UE, "
           "usage domestique), écarts identifiés, plan de mise en conformité.",
           "safety/checklist-conformite.md",
           kwargs={"subsystem_name": "Eve — conformité pré-prototype", "hazard_type": "réglementaire", "context": "marché UE visé, usage domestique"},
           refs=["safety/dossier-securite-v1.md"],
           dod=["Normes applicables listées", "Écarts identifiés", "Plan de mise en conformité"]),
        _e("RN4.4", 4, "qa_robot", "build_test_protocol",
           "Critères d'acceptation prototype physique",
           "Définis les critères d'acceptation du prototype physique Eve : critères mesurables "
           "par fonction, seuils explicites, décision go/no-go production. Synthèse finale du "
           "paper build.",
           "qa/criteres-acceptation.md",
           kwargs={"subsystem_name": "Eve — acceptation prototype physique", "risk_level": "high", "prior_issues": "checklist conformité pré-prototype"},
           refs=["qa/protocole-integration.md", "safety/dossier-securite-v1.md"],
           dod=["Critères mesurables par fonction", "Seuils explicites", "Décision go/no-go explicite"]),
    ]


def all_exercises() -> list[StudioExercise]:
    return [*_n1(), *_n2(), *_n3(), *_n4()]


def get_exercise(exercise_id: str) -> StudioExercise | None:
    for ex in all_exercises():
        if ex.exercise_id == exercise_id:
            return ex
    return None
