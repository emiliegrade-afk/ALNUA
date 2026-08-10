"use client";

import { DeptMissionsTab } from "@/components/shared/dept-missions-tab";
import type { BureauAgentDef } from "@/lib/agent-bureau";
import type { AgentStatus } from "@/lib/openroom-api";
import type { ConsoleActivityItem } from "@/lib/console/types";
import type { Project } from "@/lib/types";
import { C } from "../app-v2/shared";
import { hash, pick } from "./mock-data";

const LEVELS = ["Ville portuaire", "Forêt de Yggmar", "Donjon glacé", "Hub central", "Zone PvP"] as const;
const NPC_TAGS = ["NPC marchand", "Boss de zone", "PNJ de quête", "Garde de faction"] as const;

function gamingCardTags(ticketId: string) {
  const level = pick(`${ticketId}-lvl`, LEVELS);
  const blueprint = `BP_${(hash(`${ticketId}-bp`) % 900) + 100}`;
  const npc = hash(`${ticketId}-npc`) % 3 === 0 ? pick(`${ticketId}-npctag`, NPC_TAGS) : null;
  const chip = {
    borderColor: "rgba(224,155,106,.2)",
    color: C.warm,
  } as const;
  return (
    <>
      <span className="rounded-full border px-1.5 py-px text-[8px]" style={chip}>
        🗺 {level}
      </span>
      <span className="rounded-full border px-1.5 py-px text-[8px]" style={chip}>
        ⚙ {blueprint}
      </span>
      {npc ? (
        <span className="rounded-full border px-1.5 py-px text-[8px]" style={chip}>
          🧍 {npc}
        </span>
      ) : null}
    </>
  );
}

export function MissionsTab({
  projects,
  agents,
  statuses,
  activityFeed,
}: {
  projects: Project[];
  agents: BureauAgentDef[];
  statuses: Record<string, AgentStatus>;
  activityFeed: ConsoleActivityItem[];
}) {
  return (
    <DeptMissionsTab
      projects={projects}
      agents={agents}
      statuses={statuses}
      activityFeed={activityFeed}
      renderCardTags={gamingCardTags}
      riskDetails={["Retard estimé", "Dépendance bloquante", "Charge trop élevée"]}
    />
  );
}
