"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { BureauPage } from "@/components/shared/bureau-page";
import { AgentFocusPanel } from "@/components/openroom/agent-focus-panel";
import { LoungeHero } from "@/components/lounge/lounge-hero";
import { LoungeActivitiesGrid } from "@/components/lounge/lounge-activities-grid";
import { LoungeAgentsStrip } from "@/components/lounge/lounge-agents-strip";
import { LoungeEventsRow } from "@/components/lounge/lounge-events-row";
import { LoungeSidePanel } from "@/components/lounge/lounge-side-panel";
import { LoungePointsBadge } from "@/components/lounge/lounge-points-badge";
import { LoungePlayPanel } from "@/components/lounge/lounge-play-panel";
import type { LoungeActivityId } from "@/components/lounge/lounge-constants";
import { BUREAU_AGENTS } from "@/lib/agent-bureau";
import {
  fetchAgentsStatus,
  type AgentStatus,
} from "@/lib/openroom-api";

const LOUNGE_AGENTS = BUREAU_AGENTS.map((agent) => ({
  id: agent.id,
  name: agent.name,
  emoji: agent.icon,
  role: agent.role.split("—")[0]?.trim() ?? agent.role,
  branch: agent.branch,
}));

const POLL_MS = 12_000;

/**
 * Layout maquette :
 *   hero + activités | panneau
 *   agents / events pleine largeur
 */
export default function LoungePage() {
  const searchParams = useSearchParams();
  const [agentStatuses, setAgentStatuses] = useState<Record<string, AgentStatus>>(
    {},
  );
  const [focusedAgent, setFocusedAgent] = useState<string | null>(null);
  const [statusError, setStatusError] = useState<string | null>(null);
  const [playActivity, setPlayActivity] = useState<LoungeActivityId | null>(
    null,
  );
  const [panelKey, setPanelKey] = useState(0);

  useEffect(() => {
    const fromQuery = searchParams.get("agent");
    if (fromQuery && LOUNGE_AGENTS.some((a) => a.id === fromQuery)) {
      setFocusedAgent(fromQuery);
    }
  }, [searchParams]);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      const result = await fetchAgentsStatus();
      if (cancelled) return;
      setStatusError(result.ok ? null : result.error);
      setAgentStatuses(result.data.agents);
    }

    void poll();
    const interval = setInterval(() => {
      void poll();
    }, POLL_MS);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const focused = focusedAgent
    ? LOUNGE_AGENTS.find((a) => a.id === focusedAgent)
    : null;

  return (
    <BureauPage
      dept="lounge"
      title="Agent Lounge"
      subtitle="Détente, jeu, apprentissage & connexion"
      hideActivityRail
      className="!space-y-5"
      actions={<LoungePointsBadge />}
    >
      {statusError ? (
        <p className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-200">
          {statusError}
        </p>
      ) : null}

      <div className="grid grid-cols-1 items-start gap-5 lg:grid-cols-[minmax(0,1fr)_300px] xl:grid-cols-[minmax(0,1fr)_320px]">
        <div className="flex min-w-0 flex-col gap-5">
          <LoungeHero />
          <LoungeActivitiesGrid onPlay={setPlayActivity} />
        </div>
        <LoungeSidePanel
          agents={LOUNGE_AGENTS}
          statuses={agentStatuses}
          refreshKey={panelKey}
        />
      </div>

      <LoungeAgentsStrip
        agents={LOUNGE_AGENTS}
        statuses={agentStatuses}
        onSelect={setFocusedAgent}
      />
      <LoungeEventsRow />

      {playActivity ? (
        <LoungePlayPanel
          open
          activity={playActivity}
          onClose={() => setPlayActivity(null)}
          onSessionChange={() => setPanelKey((k) => k + 1)}
        />
      ) : null}

      {focused && focusedAgent ? (
        <AgentFocusPanel
          agent={focused}
          status={agentStatuses[focusedAgent] ?? { status: "idle" }}
          onClose={() => setFocusedAgent(null)}
        />
      ) : null}
    </BureauPage>
  );
}
