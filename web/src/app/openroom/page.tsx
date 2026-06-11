"use client";

import { useEffect, useState } from "react";
import { BackToLobby } from "@/components/shared/back-to-lobby";
import { AgentAvatar } from "@/components/openroom/agent-avatar";
import { AgentFocusPanel } from "@/components/openroom/agent-focus-panel";
import {
  countActiveAgents,
  fetchAgentsStatus,
  type AgentStatus,
  type OpenRoomLogEntry,
} from "@/lib/openroom-api";

const AGENTS = [
  {
    id: "coo",
    name: "COO",
    emoji: "👑",
    role: "Direction",
    branch: "hub" as const,
  },
  {
    id: "pm",
    name: "PM",
    emoji: "📋",
    role: "Pipeline",
    branch: "hub" as const,
  },
  {
    id: "qa",
    name: "QA",
    emoji: "🔍",
    role: "Qualité",
    branch: "hub" as const,
  },
  {
    id: "spec",
    name: "Spec",
    emoji: "📐",
    role: "Architecture",
    branch: "hub" as const,
  },
  {
    id: "dev_app",
    name: "Dev App",
    emoji: "💻",
    role: "Pôle App",
    branch: "app" as const,
  },
  {
    id: "content",
    name: "Content",
    emoji: "✍️",
    role: "Pôle App",
    branch: "app" as const,
  },
  {
    id: "marketing",
    name: "Marketing",
    emoji: "📣",
    role: "Marketing",
    branch: "hub" as const,
  },
  {
    id: "game_dir",
    name: "Game Dir.",
    emoji: "🎮",
    role: "Pôle Gaming",
    branch: "gaming" as const,
  },
  {
    id: "dev_game",
    name: "Dev Gaming",
    emoji: "🕹️",
    role: "Pôle Gaming",
    branch: "gaming" as const,
  },
  {
    id: "hardware",
    name: "Hardware",
    emoji: "🤖",
    role: "Pôle Robo",
    branch: "robo" as const,
  },
];

const POLL_MS = 3000;

export default function OpenRoomPage() {
  const [agentStatuses, setAgentStatuses] = useState<
    Record<string, AgentStatus>
  >({});
  const [logs, setLogs] = useState<OpenRoomLogEntry[]>([]);
  const [pipelineActive, setPipelineActive] = useState(false);
  const [focusedAgent, setFocusedAgent] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function poll() {
      const data = await fetchAgentsStatus();
      if (cancelled) return;
      setAgentStatuses(data.agents);
      setLogs(data.recentLogs);
      setPipelineActive(data.pipelineActive);
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

  return (
    <>
      <BackToLobby />

      <header className="mb-8">
        <h1 className="font-title text-3xl text-ivory">
          OpenRoom <span className="text-copper">ALNUA</span>
        </h1>
        <p className="mt-2 font-body text-sm text-titanium">
          {activeCount} agent{activeCount !== 1 ? "s" : ""} actif
          {activeCount !== 1 ? "s" : ""}
          {pipelineActive ? " · Pipeline en cours" : ""}
        </p>
      </header>

      <div className="mb-12 grid grid-cols-2 gap-8 sm:grid-cols-3 lg:grid-cols-5">
        {AGENTS.map((agent) => (
          <AgentAvatar
            key={agent.id}
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

      {focusedAgent ? (
        <AgentFocusPanel
          agent={AGENTS.find((a) => a.id === focusedAgent)!}
          status={agentStatuses[focusedAgent] ?? { status: "idle" }}
          onClose={() => setFocusedAgent(null)}
        />
      ) : null}
    </>
  );
}
