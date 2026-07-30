import type { GamingBuild } from "@/lib/types";
import { hubFetch } from "./hub-fetch";

export async function fetchGamingBuilds(projectId: string, limit = 20): Promise<GamingBuild[]> {
  const qs = new URLSearchParams({ project_id: projectId, limit: String(limit) });
  return hubFetch<GamingBuild[]>(`/gaming/builds?${qs.toString()}`);
}

/** Dernier build rapporté pour un projet, ou null si aucun n'existe encore. */
export async function fetchLatestGamingBuild(projectId: string): Promise<GamingBuild | null> {
  const builds = await fetchGamingBuilds(projectId, 1);
  return builds[0] ?? null;
}
