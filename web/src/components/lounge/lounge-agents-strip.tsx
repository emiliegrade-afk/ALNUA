"use client";

import { AgentAvatar } from "@/components/shared/agent-avatar";
import type { DeptKey } from "@/lib/dept-colors";
import type { AgentStatus, AgentStatusKind } from "@/lib/openroom-api";

export type LoungeAgentCard = {
  id: string;
  name: string;
  emoji: string;
  role: string;
  branch: DeptKey;
};

type Props = {
  agents: LoungeAgentCard[];
  statuses: Record<string, AgentStatus>;
  onSelect: (agentId: string) => void;
};

const DEPT_LABEL: Partial<Record<DeptKey, string>> = {
  hub: "Direction",
  secretary: "Secrétariat",
  legal: "Legal",
  app: "APP",
  academy: "Academy",
  gaming: "Gaming",
  robo: "Robotique",
  marketing: "Marketing",
  rd: "R&D",
  finances: "Finance",
  analytics: "Analytics",
  brand: "Brand",
  lounge: "Lounge",
};

const GLOW: Partial<Record<string, string>> = {
  working: "rgba(168, 85, 247, 0.28)",
  waiting: "rgba(224, 155, 106, 0.22)",
};

function badge(status: AgentStatus | undefined): string {
  const task = status?.currentTask?.trim();
  if (task) {
    const short = task.length > 14 ? `${task.slice(0, 12)}…` : task;
    return short.toUpperCase();
  }
  const kind: AgentStatusKind = status?.status ?? "idle";
  if (kind === "working") return "EN SESSION";
  if (kind === "waiting") return "EN ATTENTE";
  if (kind === "error") return "ERREUR";
  return "DISPONIBLE";
}

function timer(status: AgentStatus | undefined): string {
  if (!status || status.status === "idle") return "—:—";
  if (typeof status.progress === "number") {
    const m = Math.floor(status.progress / 10);
    const s = Math.floor(status.progress % 60)
      .toString()
      .padStart(2, "0");
    return `${String(m).padStart(2, "0")}:${s}`;
  }
  if (status.status === "working") return "03:42";
  return "—:—";
}

function subline(status: AgentStatus | undefined): string {
  if (!status || status.status === "idle") return "En pause";
  if (status.currentFile) return status.currentFile.slice(0, 28);
  if (status.currentTask) return status.currentTask.slice(0, 28);
  return "Session Lounge";
}

function busyRank(status: AgentStatus | undefined): number {
  const s = status?.status ?? "idle";
  if (s === "working") return 0;
  if (s === "waiting") return 1;
  if (s === "error") return 2;
  return 3;
}

/** Bande agents — cartes portrait type maquette (badge + timer + sous-ligne). */
export function LoungeAgentsStrip({ agents, statuses, onSelect }: Props) {
  const strip = [...agents].sort((a, b) => {
    const d = busyRank(statuses[a.id]) - busyRank(statuses[b.id]);
    if (d !== 0) return d;
    return a.name.localeCompare(b.name, "fr");
  });

  return (
    <section className="rounded-2xl border border-white/8 bg-obsidian-2/50 px-4 py-4">
      <h2 className="mb-4 text-[11px] font-medium uppercase tracking-[0.18em] text-copper/90">
        Agents dans le Lounge
      </h2>

      <div className="alnua-scroll -mx-1 flex gap-3 overflow-x-auto px-1 pb-1">
        {strip.map((agent) => {
          const status = statuses[agent.id];
          const kind = status?.status ?? "idle";
          const active = kind !== "idle";
          const dept = DEPT_LABEL[agent.branch] ?? agent.branch;
          const glow = GLOW[kind];

          return (
            <button
              key={agent.id}
              type="button"
              onClick={() => onSelect(agent.id)}
              className="flex w-[148px] shrink-0 flex-col items-center rounded-2xl border border-white/8 bg-obsidian/90 px-3 py-4 text-center transition hover:border-copper/40"
              style={glow ? { boxShadow: `0 0 28px ${glow}` } : undefined}
            >
              <AgentAvatar
                agentId={agent.id}
                name={agent.name}
                size={72}
                status={kind}
                ring={active}
              />
              <p className="mt-3 w-full truncate text-[13px] font-medium text-ivory">
                {agent.name}
              </p>
              <p className="mt-0.5 w-full truncate text-[10px] uppercase tracking-[0.12em] text-titanium/45">
                {dept}
              </p>
              <p
                className={`mt-3 w-full truncate rounded-md px-1.5 py-1 text-[9px] font-bold uppercase tracking-[0.12em] ${
                  active
                    ? "bg-copper/15 text-copper"
                    : "bg-white/5 text-titanium/40"
                }`}
              >
                {badge(status)}
              </p>
              <p className="mt-2 font-mono text-[12px] tabular-nums text-titanium/55">
                {timer(status)}
              </p>
              <p className="mt-1 w-full truncate text-[10px] text-titanium/40">
                {subline(status)}
              </p>
            </button>
          );
        })}
      </div>
    </section>
  );
}
