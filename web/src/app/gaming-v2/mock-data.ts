/* Gaming — générateurs de données placeholder.
 *
 * Décision du 2026-07-31 (plan Gaming/Robotique, réponse "roster visuel pour
 * l'instant") : l'équipe Gaming affichée ici (10 rôles) dépasse largement les
 * 3 agents réels du Hub (Mira Chen/Game Director, Nova Fischer/Dev,
 * Finn Larsen/Level Designer) — les 7 rôles restants sont des postes vacants
 * (voir page.tsx), pas de faux agents. Toutes les métriques ci-dessous
 * (branche Git, FPS, build UE5, draw calls, Steam Wishlist...) n'existent nulle
 * part dans le Hub : dérivées de façon stable (hash), jamais Math.random(),
 * pour ne pas changer à chaque rendu. À remplacer le jour où un vrai pipeline
 * de télémétrie/build existe.
 */

export function hash(seed: string): number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  return h;
}

export function pick<T>(seed: string, arr: readonly T[]): T {
  return arr[hash(seed) % arr.length];
}

export function pct(seed: string, min: number, max: number): number {
  return min + (hash(seed) % (max - min + 1));
}

// Version réelle du moteur utilisée par le studio — pas un placeholder. Sert
// de repli d'affichage tant qu'aucun build réel n'a été rapporté (Phase 16,
// ROADMAP.md, gaming_builds) — voir @/lib/gaming-builds.
export const UE5_VERSION = "5.8";

/* agentBuildInfo (branche/build/UE5/dernier commit par agent) et les champs
 * version/build/fps/crashes de projectStats ont été retirés en Phase 16
 * (ROADMAP.md, 2026-07-30) — remplacés par le dernier build réel rapporté
 * via @/lib/gaming-builds (aucun pipeline UE5 réel n'existe encore, donc
 * l'UI affiche un état vide honnête tant qu'aucun build n'a été poussé).
 * bugs/features ci-dessous restent provisoires — hors scope de cette phase. */
export interface GamingProjectStats {
  bugs: number;
  features: number;
}

export function projectStats(projectId: string): GamingProjectStats {
  const seed = `gaming-proj-${projectId}`;
  return {
    bugs: pct(`${seed}-bugs`, 3, 40),
    features: pct(`${seed}-feat`, 20, 90),
  };
}
