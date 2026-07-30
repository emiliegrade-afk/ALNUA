/* Robotique — générateurs de données placeholder.
 *
 * Réponse "roster visuel pour l'instant" (2026-07-31, plan Gaming/Robotique) :
 * l'équipe affichée ici (10 rôles) dépasse largement les 2 agents réels du
 * Hub (Yuki Tanaka/Hardware, Zara Singh/Embedded) — les 8 rôles restants sont
 * des postes vacants (voir page.tsx), pas de faux agents. Toutes les
 * métriques ci-dessous (BOM, PCB, certification, consommation, batterie...)
 * n'existent nulle part dans le Hub : dérivées de façon stable (hash),
 * jamais Math.random(). À remplacer le jour où un vrai pipeline de suivi
 * hardware existe. */

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

/* agentBuildInfo/BUILD_BRANCHES/STAGES et projectStats/RoboProjectStats ont
 * été retirés en Phases 19-20 (ROADMAP.md, 2026-07-30) — remplacés par les
 * vraies données rapportées (robo_builds, robo_lab_tests, robo_telemetry) via
 * @/lib/robo-builds, @/lib/robo-lab-tests, @/lib/robo-telemetry. */
