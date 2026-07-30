import type { GamingCommunityStats } from "@/lib/types";
import { hubFetch } from "./hub-fetch";

export async function fetchGamingCommunityStats(): Promise<GamingCommunityStats> {
  return hubFetch<GamingCommunityStats>("/gaming/community-stats");
}
