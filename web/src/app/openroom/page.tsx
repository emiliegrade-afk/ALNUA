"use client";

import { useEffect, useState } from "react";
import { BureauPage } from "@/components/shared/bureau-page";
import { OpenRoomAgentTile } from "@/components/openroom/openroom-agent-tile";
import { AgentFocusPanel } from "@/components/openroom/agent-focus-panel";
import { BUREAU_AGENTS } from "@/lib/agent-bureau";
import {
  countActiveAgents,
  fetchAgentsStatus,
  type AgentStatus,
  type OpenRoomLogEntry,
} from "@/lib/openroom-api";

const OPENROOM_AGENTS = BUREAU_AGENTS.map((agent) => ({
  id: agent.id,
  name: agent.name.split(" ")[0],
  emoji: agent.icon,
  role: agent.role.split("—")[0]?.trim() ?? agent.role,
  branch: agent.branch,
}));

const POLL_MS = 12_000;

export default function OpenRoomPage() {
  const [agentStatuses, setAgentStatuses] = useState<
    Record<string, AgentStatus>
  >({});
  const [logs, setLogs] = useState<OpenRoomLogEntry[]>([]);
  const [pipelineActive, setPipelineActive] = useState(false);
  const [focusedAgent, setFocusedAgent] = useState<string | null>(null);

  const [statusError, setStatusError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      const result = await fetchAgentsStatus();
      if (cancelled) return;
      setStatusError(result.ok ? null : result.error);
      setAgentStatuses(result.data.agents);
      setLogs(result.data.recentLogs);
      setPipelineActive(result.data.pipelineActive);
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

  const activeCount = countActiveAgents(agentStatuses);
  const focused = focusedAgent
    ? OPENROOM_AGENTS.find((a) => a.id === focusedAgent)
    : null;

  const subtitle = `${activeCount} agent${activeCount !== 1 ? "s" : ""} actif${
    activeCount !== 1 ? "s" : ""
  }${pipelineActive ? " · Pipeline en cours" : ""}`;

  return (
    <BureauPage dept="openroom" title="OpenRoom" subtitle={subtitle}>
      {statusError ? (
        <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 font-body text-sm text-amber-200">
          {statusError}
        </p>
      ) : null}

      <div className="grid grid-cols-2 gap-8 sm:grid-cols-3 lg:grid-cols-5">
        {OPENROOM_AGENTS.map((agent) => (
          <OpenRoomAgentTile
            key={agent.id}
            id={agent.id}
            name={agent.name}
            role={agent.role}
            emoji={agent.emoji}
            branch={agent.branch}
            status={agentStatuses[agent.id]?.status ?? "idle"}
            currentTask={agentStatuses[agent.id]?.currentTask}
            onClick={() => setFocusedAgent(agent.id)}
          />
        ))}
      </div>

      <div className="rounded-xl border border-copper/15 bg-obsidian-2 p-4">
        <h3 className="label-caps mb-3">Log temps réel</h3>
        <div className="max-h-64 space-y-1 overflow-y-auto font-mono text-xs">
          {logs.map((log, i) => (
            <div key={`${log.time}-${log.agent}-${i}`} className="flex gap-3 text-titanium">
              <span className="shrink-0 text-copper/60">{log.time}</span>
              <span className="w-12 shrink-0 text-copper">{log.agent}</span>
              <span>{log.message}</span>
            </div>
          ))}
          {logs.length === 0 ? (
            <p className="text-titanium/40">
              Aucune activité — les agents dorment 💤
            </p>
          ) : null}
        </div>
      </div>

      {focused ? (
        <AgentFocusPanel
          agent={focused}
          status={agentStatuses[focusedAgent!] ?? { status: "idle" }}
          onClose={() => setFocusedAgent(null)}
        />
      ) : null}
    </BureauPage>
  );
}
