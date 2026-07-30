import type { GamingAsset } from "@/lib/types";
import { hubFetch } from "./hub-fetch";

export async function fetchGamingAssets(projectId: string): Promise<GamingAsset[]> {
  const qs = new URLSearchParams({ project_id: projectId });
  return hubFetch<GamingAsset[]>(`/gaming/assets?${qs.toString()}`);
}
