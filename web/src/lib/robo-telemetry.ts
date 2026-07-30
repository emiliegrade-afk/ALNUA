import type { RoboTelemetry } from "@/lib/types";
import { hubFetch } from "./hub-fetch";

export async function fetchRoboTelemetry(projectId: string, limit = 1): Promise<RoboTelemetry[]> {
  const qs = new URLSearchParams({ project_id: projectId, limit: String(limit) });
  return hubFetch<RoboTelemetry[]>(`/robo/telemetry?${qs.toString()}`);
}

export async function fetchLatestRoboTelemetry(projectId: string): Promise<RoboTelemetry | null> {
  const rows = await fetchRoboTelemetry(projectId, 1);
  return rows[0] ?? null;
}
