import type { RoboBuild } from "@/lib/types";
import { hubFetch } from "./hub-fetch";

export async function fetchRoboBuilds(projectId: string, limit = 20): Promise<RoboBuild[]> {
  const qs = new URLSearchParams({ project_id: projectId, limit: String(limit) });
  return hubFetch<RoboBuild[]>(`/robo/builds?${qs.toString()}`);
}

export async function fetchLatestRoboBuild(projectId: string): Promise<RoboBuild | null> {
  const builds = await fetchRoboBuilds(projectId, 1);
  return builds[0] ?? null;
}
