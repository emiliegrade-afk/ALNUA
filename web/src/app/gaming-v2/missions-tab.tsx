"use client";

import { DeptMissionsTab } from "@/components/shared/dept-missions-tab";
import type { BureauAgentDef } from "@/lib/agent-bureau";
import type { AgentStatus } from "@/lib/openroom-api";
import type { ConsoleActivityItem } from "@/lib/console/types";
import type { Project } from "@/lib/types";

/** Missions Gaming — tickets Kanban réels, sans tags décoratifs inventés. */
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
    />
  );
}
