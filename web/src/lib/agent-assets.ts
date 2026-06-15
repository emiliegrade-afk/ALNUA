import type { AgentStatusKind } from "@/lib/openroom-api";

export interface AgentOfficeAssets {
  portrait: string;
  /**
   * Runway Act-Two character performance loops only.
   * Do NOT use procedural warp previews here — they shift a static image,
   * not real facial/body animation.
   */
  actTwoLoops?: Partial<Record<AgentStatusKind, string>>;
}

/** Static portrait + optional Act-Two loops from /public/agents/{id}/ */
export const AGENT_OFFICE_ASSETS: Partial<Record<string, AgentOfficeAssets>> = {
  coo: {
    portrait: "/agents/coo/office.png",
    // Drop Act-Two exports here when ready:
    // actTwoLoops: {
    //   idle: "/agents/coo/idle-acttwo.webm",
    //   working: "/agents/coo/working-acttwo.webm",
    //   waiting: "/agents/coo/idle-acttwo.webm",
    //   error: "/agents/coo/alert-acttwo.webm",
    // },
  },
};

export function getAgentOfficeAssets(agentId: string): AgentOfficeAssets | null {
  return AGENT_OFFICE_ASSETS[agentId] ?? null;
}

export function hasActTwoLoops(agentId: string): boolean {
  const assets = getAgentOfficeAssets(agentId);
  if (!assets?.actTwoLoops) return false;
  return Object.values(assets.actTwoLoops).some(Boolean);
}

/** Returns Act-Two loop URL only when real performance capture exists. */
export function getAgentLoopSrc(
  agentId: string,
  status: AgentStatusKind,
): string | null {
  const assets = getAgentOfficeAssets(agentId);
  if (!assets?.actTwoLoops) return null;
  return assets.actTwoLoops[status] ?? assets.actTwoLoops.idle ?? null;
}
