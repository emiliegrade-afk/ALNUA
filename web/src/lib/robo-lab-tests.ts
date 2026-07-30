import type { RoboLabTest } from "@/lib/types";
import { hubFetch } from "./hub-fetch";

export async function fetchRoboLabTests(projectId: string): Promise<RoboLabTest[]> {
  const qs = new URLSearchParams({ project_id: projectId });
  return hubFetch<RoboLabTest[]>(`/robo/lab-tests?${qs.toString()}`);
}
