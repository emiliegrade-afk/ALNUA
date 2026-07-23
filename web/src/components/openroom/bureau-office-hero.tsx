"use client";

import { AgentOfficeAvatar } from "@/components/openroom/agent-office-avatar";
import { getAgentById } from "@/lib/agent-bureau";
import { getAgentOfficeAssets } from "@/lib/agent-assets";
import { useAgentStatuses } from "@/hooks/use-agent-statuses";

interface BureauOfficeHeroProps {
  agentId: string;
}

export function BureauOfficeHero({ agentId }: BureauOfficeHeroProps) {
  const agent = getAgentById(agentId);
  const assets = getAgentOfficeAssets(agentId);
  const agentStatuses = useAgentStatuses();
  const live = agentStatuses[agentId];

  if (!agent || !assets) return null;

  return (
    <section className="mb-8 grid gap-6 lg:grid-cols-[minmax(260px,320px)_1fr] lg:items-start">
      <AgentOfficeAvatar
        agentId={agentId}
        name={agent.name}
        role={agent.role}
        branch={agent.branch}
        status={live?.status ?? "idle"}
        currentTask={live?.currentTask}
        variant="large"
      />
      <div className="flex flex-col justify-center rounded-2xl border border-bronze-faint bg-obsidian/70 p-6">
        <p className="label-caps mb-2 text-bronze">Bureau de Direction</p>
        <h2 className="font-title text-2xl text-ivoire">{agent.name}</h2>
        <p className="mt-1 text-sm text-titane">{agent.role}</p>
        <p className="mt-4 max-w-xl font-body text-sm leading-relaxed text-titane/90">
          {agent.description}
        </p>
        <p className="mt-4 text-xs text-titane/50">
          Portrait bureau — les boucles Act-Two (vraie animation) remplaceront le statique
          une fois générées via Runway.
        </p>
      </div>
    </section>
  );
}
