/* Détail projet — générateurs de données placeholder.
 *
 * Le Hub ne suit aujourd'hui ni phases de projet, ni modules/fonctionnalités,
 * ni décisions en attente, ni stats individuelles d'agent (disponibilité,
 * ancienneté, localisation, qualité de code...). Reproduire la maquette
 * demande donc des valeurs de remplacement — décision explicite (2026-07-29:
 * "même si les fonctions n'existent pas encore, copie exactement, les
 * fonctions vont être créées après"). Tout est dérivé de manière stable
 * (hash de l'id réel) pour ne pas changer à chaque rendu ; rien n'est
 * `Math.random()`. Le jour où un vrai système de suivi existe, ces fonctions
 * sont le seul endroit à réécrire. */

function hash(seed: string): number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  return h;
}

function pick<T>(seed: string, arr: readonly T[]): T {
  return arr[hash(seed) % arr.length];
}

function pct(seed: string, min: number, max: number): number {
  return min + (hash(seed) % (max - min + 1));
}

/* Les phases/modules varient par nature de projet (branch) — un jeu et une
 * app mobile n'ont pas le même pipeline. Toujours dérivé, jamais réel. */
const PHASES_BY_BRANCH = {
  app: ["Recherche", "UX / UI", "Frontend", "Backend", "QA", "Publication"],
  gaming: ["Concept", "Prototype", "Production", "Alpha", "Beta", "Release"],
  robotics: ["Recherche", "Conception", "Prototype", "Tests", "Certification", "Production"],
  other: ["Recherche", "Conception", "Développement", "Tests", "Publication"],
} as const;

export function phasesFor(branch: string): readonly string[] {
  return PHASES_BY_BRANCH[branch as keyof typeof PHASES_BY_BRANCH] ?? PHASES_BY_BRANCH.other;
}

/* Le bouton "Retour" doit ramener au département d'origine du projet, pas
 * toujours à /app. Robotique n'a pas encore sa propre page dédiée (comme
 * /gaming-v2) — /robo reste la page réelle en attendant sa refonte. */
const BACK_ROUTE_BY_BRANCH: Record<string, string> = {
  app: "/app",
  gaming: "/gaming",
  robotics: "/robo",
  other: "/app",
};

export function backRouteFor(branch: string): string {
  return BACK_ROUTE_BY_BRANCH[branch] ?? "/app";
}

export function phaseProgress(projectId: string, branch: string): number[] {
  const phases = phasesFor(branch);
  // Décroissant vers l'aval du pipeline — cohérent avec un projet en cours.
  return phases.map((phase, i) => {
    const base = 100 - i * 16;
    return Math.max(4, Math.min(100, base - pct(`${projectId}-${phase}`, 0, 10)));
  });
}

/* decisionsEnAttente/MockDecision ont été retirés en Phase 15 (ROADMAP.md,
 * 2026-07-30) — remplacés par les items roadmap réels (statut idea/planned)
 * du projet, via @/lib/roadmap. Voir page.tsx. */

export function coordinatorInsight(projectId: string, projectName: string, branch: string): string {
  const phases = phasesFor(branch);
  const bottleneck = pick(`${projectId}-bottleneck`, phases);
  return `Le rythme de ${projectName} est stable. ${bottleneck} concentre la charge la plus élevée en ce moment — surveiller les délais de cette phase.`;
}

/* modulesForProject/MockModule ont été retirés en Phase 14 (ROADMAP.md,
 * 2026-07-30) — remplacés par la vraie table `project_modules` (voir
 * @/lib/modules). featuresForModule/dependenciesForModule ci-dessous restent
 * provisoires : il n'existe pas encore de table pour le détail ligne par
 * ligne (sous-fonctionnalités, dépendances) à l'intérieur d'un module. */

export interface MockFeatureRow {
  name: string;
  status: "Terminé" | "En cours" | "À faire" | "En test";
  responsible: string;
  progress: number;
}

export function featuresForModule(moduleId: string, agentNames: string[]): MockFeatureRow[] {
  const rows = ["Scan / capture", "Analyse", "Recommandations", "Historique", "Objectifs", "Intégration externe"];
  const statuses = ["Terminé", "En cours", "À faire", "En test"] as const;
  return rows.map((r) => {
    const seed = `${moduleId}-feat-${r}`;
    return {
      name: r,
      status: pick(seed, statuses),
      responsible: agentNames.length > 0 ? pick(seed, agentNames) : "—",
      progress: pct(seed, 0, 100),
    };
  });
}

export function dependenciesForModule(moduleId: string): { label: string; status: "Terminé" | "En cours" }[] {
  const deps = ["Authentification", "Profil utilisateur", "Base de données", "API externe"];
  return deps.map((d) => ({
    label: d,
    status: pct(`${moduleId}-dep-${d}`, 0, 1) === 1 ? "En cours" : "Terminé",
  }));
}

export interface MockAgentStats {
  availability: number;
  currentLoad: number;
  tenureMonths: number;
  location: string;
  languages: string;
  missionsDone: number;
  codeQuality: number;
  onTime: number;
  collaboration: number;
  skills: { label: string; value: number }[];
}

export function agentStats(agentId: string, skills: string[]): MockAgentStats {
  const seed = `agent-${agentId}`;
  return {
    availability: pct(`${seed}-avail`, 40, 95),
    currentLoad: pct(`${seed}-load`, 30, 90),
    tenureMonths: pct(`${seed}-tenure`, 3, 40),
    location: pick(`${seed}-loc`, ["Europe/Paris", "Europe/Bruxelles", "Europe/Lisbonne", "UTC"] as const),
    languages: pick(`${seed}-lang`, ["FR · EN", "FR · EN · ES", "EN · DE"] as const),
    missionsDone: pct(`${seed}-missions`, 8, 60),
    codeQuality: pct(`${seed}-quality`, 80, 99),
    onTime: pct(`${seed}-ontime`, 75, 99),
    collaboration: pct(`${seed}-collab`, 80, 99),
    skills: skills.map((s, i) => ({ label: s, value: Math.max(55, 95 - i * 8 - (hash(seed + s) % 6)) })),
  };
}
