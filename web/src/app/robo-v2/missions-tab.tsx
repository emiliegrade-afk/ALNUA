"use client";

import { DeptMissionsTab } from "@/components/shared/dept-missions-tab";
import type { BureauAgentDef } from "@/lib/agent-bureau";
import type { AgentStatus } from "@/lib/openroom-api";
import type { ConsoleActivityItem } from "@/lib/console/types";
import type { Project } from "@/lib/types";
import { C } from "../app-v2/shared";
import { hash, pick } from "./mock-data";

const COMPONENTS = ["Servo X2", "Carte PCB v3", "Batterie Li-ion", "Caméra IA", "Capteur LiDAR", "Châssis alu"] as const;
const BENCHES = ["Banc thermique", "Banc vibratoire", "Banc électrique", "Salle blanche"] as const;

function roboCardTags(ticketId: string) {
  const component = pick(`${ticketId}-comp`, COMPONENTS);
  const bench = hash(`${ticketId}-bench`) % 2 === 0 ? pick(`${ticketId}-benchtag`, BENCHES) : null;
  const chip = {
    borderColor: "rgba(224,155,106,.2)",
    color: C.warm,
  } as const;
  return (
    <>
      <span className="rounded-full border px-1.5 py-px text-[8px]" style={chip}>
        🔧 {component}
      </span>
      {bench ? (
        <span className="rounded-full border px-1.5 py-px text-[8px]" style={chip}>
          🧪 {bench}
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
      renderCardTags={roboCardTags}
      riskDetails={["Délai fournisseur", "Composant en rupture", "Certification bloquante"]}
    />
  );
}
