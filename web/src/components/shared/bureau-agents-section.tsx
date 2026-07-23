"use client";

import { useState } from "react";
import { AgentCard } from "@/components/shared/agent-card";
import { AgentFocusPanel } from "@/components/openroom/agent-focus-panel";
import { BureauLibraryPopup } from "@/components/library/bureau-library-popup";
import {
  getAgentById,
  getAgentsForBureau,
  type BureauAgentDef,
  type BureauKey,
} from "@/lib/agent-bureau";
import { useAgentStatuses } from "@/hooks/use-agent-statuses";

interface BureauAgentsSectionProps {
  bureau: BureauKey;
  /** Optional per-agent overrides (e.g. dynamic badge) */
  mapAgent?: (agent: BureauAgentDef) => BureauAgentDef & { badge?: string };
  /** Hide agents already shown elsewhere (e.g. bureau hero) */
  excludeAgentIds?: string[];
  /** Show bureau library shelf below agents */
  showLibrary?: boolean;
  className?: string;
}

export function BureauAgentsSection({
  bureau,
  mapAgent,
  excludeAgentIds = [],
  showLibrary = true,
  className,
}: BureauAgentsSectionProps) {
  const [focusedAgentId, setFocusedAgentId] = useState<string | null>(null);
  const agentStatuses = useAgentStatuses();

  const agents = getAgentsForBureau(bureau)
    .filter((a) => !excludeAgentIds.includes(a.id))
    .map((a) => mapAgent?.(a) ?? a);

  const focused = focusedAgentId ? getAgentById(focusedAgentId) : null;

  return (
    <>
      <section
        className={
          className ??
          `mb-8 grid gap-4 sm:grid-cols-2${agents.length >= 3 ? " lg:grid-cols-3" : ""}`
        }
      >
        {agents.map((agent) => (
          <AgentCard
            key={agent.id}
            icon={agent.icon}
            name={agent.name}
            role={agent.role}
            branch={agent.branch}
            description={agent.description}
            skills={agent.skills}
            badge={"badge" in agent ? (agent as BureauAgentDef & { badge?: string }).badge : undefined}
            status={agentStatuses[agent.id]?.status ?? "idle"}
            currentTask={agentStatuses[agent.id]?.currentTask}
            onClick={() => setFocusedAgentId(agent.id)}
          />
        ))}
      </section>

      {showLibrary ? <BureauLibraryPopup bureau={bureau} /> : null}

      {focused ? (
        <AgentFocusPanel
          agent={{
            id: focused.id,
            name: focused.name,
            emoji: focused.icon,
            role: focused.role,
            branch: focused.branch,
          }}
          status={agentStatuses[focused.id] ?? { status: "idle" }}
          onClose={() => setFocusedAgentId(null)}
        />
      ) : null}
    </>
  );
}
