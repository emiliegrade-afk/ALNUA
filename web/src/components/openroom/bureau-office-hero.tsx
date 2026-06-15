"use client";

import { useEffect, useState } from "react";
import { AgentOfficeAvatar } from "@/components/openroom/agent-office-avatar";
import { getAgentById } from "@/lib/agent-bureau";
import { getAgentOfficeAssets } from "@/lib/agent-assets";
import { fetchAgentsStatus, type AgentStatusKind } from "@/lib/openroom-api";

const POLL_MS = 3000;

interface BureauOfficeHeroProps {
  agentId: string;
}

export function BureauOfficeHero({ agentId }: BureauOfficeHeroProps) {
  const agent = getAgentById(agentId);
  const assets = getAgentOfficeAssets(agentId);
  const [status, setStatus] = useState<AgentStatusKind>("idle");
  const [currentTask, setCurrentTask] = useState<string | undefined>();

  useEffect(() => {
    if (!assets) return;
    let cancelled = false;
    let intervalId: ReturnType<typeof setInterval> | undefined;

    async function poll() {
      const result = await fetchAgentsStatus();
      if (cancelled) return;
      const live = result.data.agents[agentId];
      setStatus(live?.status ?? "idle");
      setCurrentTask(live?.currentTask);
    }

    const start = () => {
      void poll();
      intervalId = setInterval(() => void poll(), POLL_MS);
    };

    if (typeof requestIdleCallback !== "undefined") {
      const idleId = requestIdleCallback(start, { timeout: 600 });
      return () => {
        cancelled = true;
        cancelIdleCallback(idleId);
        if (intervalId) clearInterval(intervalId);
      };
    }

    const timeoutId = setTimeout(start, 0);
    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
      if (intervalId) clearInterval(intervalId);
    };
  }, [agentId, assets]);

  if (!agent || !assets) return null;

  return (
    <section className="mb-8 grid gap-6 lg:grid-cols-[minmax(260px,320px)_1fr] lg:items-start">
      <AgentOfficeAvatar
        agentId={agentId}
        name={agent.name}
        role={agent.role}
        branch={agent.branch}
        status={status}
        currentTask={currentTask}
        variant="large"
      />
      <div className="flex flex-col justify-center rounded-2xl border border-copper/15 bg-obsidian-2/60 p-6">
        <p className="label-caps mb-2 text-copper">Bureau de Direction</p>
        <h2 className="font-title text-2xl text-ivory">{agent.name}</h2>
        <p className="mt-1 text-sm text-titanium">{agent.role}</p>
        <p className="mt-4 max-w-xl font-body text-sm leading-relaxed text-titanium/90">
          {agent.description}
        </p>
        <p className="mt-4 text-xs text-titanium/50">
          Portrait bureau — les boucles Act-Two (vraie animation) remplaceront le statique
          une fois générées via Runway.
        </p>
      </div>
    </section>
  );
}
