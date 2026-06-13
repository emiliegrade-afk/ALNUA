"use client";

import { useEffect, useState } from "react";
import { AgentCard } from "@/components/shared/agent-card";
import { AgentFocusPanel } from "@/components/openroom/agent-focus-panel";
import {
  getAgentById,
  getAgentsForBureau,
  type BureauAgentDef,
  type BureauKey,
} from "@/lib/agent-bureau";
import { fetchAgentsStatus, type AgentStatus } from "@/lib/openroom-api";

const POLL_MS = 3000;

interface BureauAgentsSectionProps {
  bureau: BureauKey;
  /** Optional per-agent overrides (e.g. dynamic badge) */
  mapAgent?: (agent: BureauAgentDef) => BureauAgentDef & { badge?: string };
  className?: string;
}

export function BureauAgentsSection({
  bureau,
  mapAgent,
  className,
}: BureauAgentsSectionProps) {
  const [focusedAgentId, setFocusedAgentId] = useState<string | null>(null);
  const [agentStatuses, setAgentStatuses] = useState<Record<string, AgentStatus>>({});

  const agents = getAgentsForBureau(bureau).map((a) => mapAgent?.(a) ?? a);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      const data = await fetchAgentsStatus();
      if (cancelled) return;
      setAgentStatuses(data.agents);
    }

    void poll();
    const interval = setInterval(() => void poll(), POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

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

      {focused ? (
        <AgentFocusPanel
          agent={{
            id: focused.id,
            name: focused.name,
            emoji: focused.icon,
            role: focused.role,
          }}
          status={agentStatuses[focused.id] ?? { status: "idle" }}
          onClose={() => setFocusedAgentId(null)}
        />
      ) : null}
    </>
  );
}
