"use client";

import Image from "next/image";
import Link from "next/link";
import { Radio, Server, Zap } from "lucide-react";
import { BUREAU_AGENTS, getAgentsForBureau } from "@/lib/agent-bureau";
import { getAgentOfficeAssets } from "@/lib/agent-assets";
import {
  getOfficeBadge,
  getPrimaryAgentForOffice,
  HQ_CEO_ACCESS,
  HQ_OFF_MAP_ACCESS,
  type HqOffMapAccess,
  type HqSector,
} from "@/lib/hq-hub-offices";
import { ROUTES } from "@/lib/routes";
import {
  activitySparkline,
  deptMetrics,
  pipelineBars,
} from "@/lib/lobby-monitor-utils";
import type { LobbyStats } from "@/lib/lobby-api";
import type {
  AgentStatus,
  AgentStatusKind,
  AgentsStatusResponse,
  OpenRoomLogEntry,
} from "@/lib/openroom-api";
import type { HubHealthPhase } from "@/hooks/use-hub-health-live";
import {
  HudBarChart,
  HudPanel,
  HudRingGauge,
  HudSparkline,
} from "@/components/lobby/hq-monitor-charts";
import { cn } from "@/lib/utils";

interface HqActivityMonitorPanelProps {
  stats: LobbyStats;
  agents: Record<string, AgentStatus>;
  activeAgents: number;
  recentLogs: OpenRoomLogEntry[];
  pipelineActive: boolean;
  codingPipeline?: AgentsStatusResponse["codingPipeline"];
  hubPhase: HubHealthPhase;
  selectedOffice: HqSector | null;
  onSelectOffMap?: (access: HqOffMapAccess) => void;
}

const STATUS_LABEL: Record<AgentStatusKind, string> = {
  working: "Actif",
  waiting: "Attente",
  error: "Erreur",
  idle: "Repos",
};

const STATUS_DOT: Record<AgentStatusKind, string> = {
  working: "bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.6)]",
  waiting: "bg-copper animate-pulse shadow-[0_0_6px_rgba(192,138,98,0.6)]",
  error: "bg-red-500",
  idle: "bg-titanium/30",
};

const HUB_PHASE_COPY: Record<
  HubHealthPhase,
  { label: string; className: string }
> = {
  ok: { label: "Hub OK", className: "text-emerald-400 bg-emerald-500/10" },
  checking: { label: "Sync…", className: "text-titanium/70 bg-white/5" },
  key: { label: "Clé API", className: "text-amber-300 bg-amber-500/15" },
  down: { label: "Offline", className: "text-red-300 bg-red-500/15" },
};

function agentsForOffice(office: HqSector | null) {
  if (!office) return BUREAU_AGENTS;
  if (office.bureau) return getAgentsForBureau(office.bureau);
  const primary = getPrimaryAgentForOffice(office);
  return primary ? [primary] : [];
}

function logsForOffice(
  logs: OpenRoomLogEntry[],
  office: HqSector | null,
): OpenRoomLogEntry[] {
  if (!office) return logs;
  const sectorAgents = agentsForOffice(office);
  if (sectorAgents.length === 0) return logs;
  const ids = new Set(sectorAgents.map((a) => a.id));
  const names = new Set(
    sectorAgents.map((a) => a.name.split(" ")[0].toLowerCase()),
  );
  const filtered = logs.filter(
    (log) =>
      ids.has(log.agent) ||
      names.has(log.agent.toLowerCase()) ||
      log.agent.toLowerCase().includes(office.id),
  );
  return filtered.length > 0 ? filtered : logs.slice(0, 8);
}

/** Left column — live monitoring + compact navigation. */
export function HqActivityMonitorPanel({
  stats,
  agents,
  activeAgents,
  recentLogs,
  pipelineActive,
  codingPipeline,
  hubPhase,
  selectedOffice,
  onSelectOffMap,
}: HqActivityMonitorPanelProps) {
  const sectorAgents = agentsForOffice(selectedOffice);
  const displayLogs = logsForOffice(recentLogs, selectedOffice);
  const workingInSector = sectorAgents.filter(
    (a) => agents[a.id]?.status === "working",
  ).length;
  const badge = selectedOffice ? getOfficeBadge(selectedOffice, stats) : null;
  const metrics = deptMetrics(
    selectedOffice,
    stats,
    codingPipeline,
    activeAgents,
  );
  const sparkData = activitySparkline(displayLogs);
  const pipeBars = pipelineBars(codingPipeline);
  const hubCopy = HUB_PHASE_COPY[hubPhase];

  const sortedAgents = [...sectorAgents]
    .sort((a, b) => {
      const order: Record<AgentStatusKind, number> = {
        working: 0,
        waiting: 1,
        error: 2,
        idle: 3,
      };
      const sa = agents[a.id]?.status ?? "idle";
      const sb = agents[b.id]?.status ?? "idle";
      return order[sa] - order[sb];
    })
    .slice(0, 6);

  return (
    <aside
      className="relative flex h-full select-none flex-col overflow-hidden border-r border-copper/25 bg-[#050608]/90 backdrop-blur-2xl"
      aria-label="Monitoring activité"
    >
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage:
            "repeating-linear-gradient(90deg, transparent, transparent 2px, rgba(212,168,130,0.6) 2px, rgba(212,168,130,0.6) 3px)",
        }}
      />

      <div className="relative z-10 flex shrink-0 items-center gap-2 border-b border-copper/15 px-3 py-2">
        <Radio className="h-3.5 w-3.5 shrink-0 animate-pulse text-copper" />
        <span className="font-body text-[9px] uppercase tracking-[0.28em] text-copper">
          Command Center
        </span>
        <span
          className={cn(
            "ml-auto flex items-center gap-1 rounded px-1.5 py-0.5 font-mono text-[7px] uppercase",
            hubCopy.className,
          )}
        >
          <Server className="h-2.5 w-2.5" />
          {hubCopy.label}
        </span>
      </div>

      <div className="relative z-10 flex min-h-0 flex-1 flex-col gap-1.5 overflow-y-auto p-2">
        <HudPanel title="Accès rapide" className="py-1.5">
          <div className="flex flex-wrap gap-1">
            <Link
              href={HQ_CEO_ACCESS.href}
              title={HQ_CEO_ACCESS.title}
              className="relative flex h-9 w-9 items-center justify-center overflow-hidden rounded-md border border-copper/25 bg-copper/5 transition hover:border-copper/45 hover:bg-copper/10"
            >
              <Image
                src={HQ_CEO_ACCESS.portrait ?? ""}
                alt="CEO"
                fill
                className="object-cover object-top"
                sizes="36px"
              />
              {stats.ceoNotifications > 0 ? (
                <span className="absolute -right-0.5 -top-0.5 flex h-3.5 min-w-3.5 items-center justify-center rounded-full bg-copper px-0.5 font-mono text-[7px] text-obsidian">
                  {stats.ceoNotifications}
                </span>
              ) : null}
            </Link>
            {HQ_OFF_MAP_ACCESS.map((access) => {
              const accessBadge = getOfficeBadge(access, stats);
              return (
                <button
                  key={access.id}
                  type="button"
                  title={`${access.number}. ${access.title}`}
                  onClick={() => onSelectOffMap?.(access)}
                  className={cn(
                    "relative flex h-9 w-9 items-center justify-center rounded-md border text-base transition",
                    selectedOffice?.id === access.id
                      ? "border-copper/50 bg-copper/15"
                      : "border-copper/20 bg-copper/5 hover:border-copper/35",
                  )}
                >
                  {access.icon}
                  {accessBadge.highlight ? (
                    <span className="absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-copper" />
                  ) : null}
                </button>
              );
            })}
            <Link
              href={ROUTES.openroom}
              title="OpenRoom"
              className="flex h-9 w-9 items-center justify-center rounded-md border border-copper/20 bg-copper/5 text-sm transition hover:border-copper/35"
            >
              💬
            </Link>
          </div>
        </HudPanel>

        {selectedOffice ? (
          <HudPanel title={selectedOffice.shortcutLabel}>
            <div className="flex items-center gap-2">
              <span className="text-lg leading-none">{selectedOffice.icon}</span>
              <div className="min-w-0 flex-1">
                <p className="truncate font-title text-[11px] font-medium text-ivory">
                  {selectedOffice.title}
                </p>
                {badge ? (
                  <p
                    className={cn(
                      "mt-0.5 inline-block rounded px-1 py-0.5 font-body text-[8px]",
                      badge.highlight
                        ? "bg-copper/20 text-copper"
                        : "text-titanium/60",
                    )}
                  >
                    {badge.label}
                  </p>
                ) : null}
              </div>
              <span
                className={cn(
                  "shrink-0 rounded px-1 py-0.5 font-mono text-[7px] uppercase",
                  pipelineActive
                    ? "bg-emerald-500/15 text-emerald-400"
                    : "text-titanium/40",
                )}
              >
                {pipelineActive ? "ON" : "—"}
              </span>
            </div>
          </HudPanel>
        ) : null}

        <div className="grid grid-cols-2 gap-1.5">
          <HudPanel title="Activité">
            <HudSparkline data={sparkData} />
            <p className="mt-0.5 text-center font-mono text-[7px] text-copper/50">
              {displayLogs.length} events
            </p>
          </HudPanel>
          <HudPanel title="Secteur" className="flex items-center justify-center">
            <HudRingGauge
              value={workingInSector}
              max={Math.max(sectorAgents.length, 1)}
              label="actifs"
            />
          </HudPanel>
        </div>

        <HudPanel title="Pipeline">
          <HudBarChart bars={pipeBars} />
          {(codingPipeline?.inPipelineIssues?.length ?? 0) > 0 ? (
            <ul className="mt-1.5 max-h-16 space-y-0.5 overflow-y-auto border-t border-copper/10 pt-1.5">
              {codingPipeline!.inPipelineIssues!.slice(0, 3).map((issue, i) => (
                <li
                  key={`${issue.issue_number}-${i}`}
                  className="truncate font-mono text-[7px] text-titanium/55"
                >
                  #{issue.issue_number}{" "}
                  {issue.title?.slice(0, 40) ?? issue.repo_slug}
                </li>
              ))}
            </ul>
          ) : null}
        </HudPanel>

        <HudPanel title="Agents">
          <ul className="max-h-36 space-y-1 overflow-y-auto pr-0.5">
            {sortedAgents.map((agent) => {
              const status = agents[agent.id]?.status ?? "idle";
              const task = agents[agent.id]?.currentTask;
              const assets = getAgentOfficeAssets(agent.id);

              return (
                <li
                  key={agent.id}
                  className="flex items-center gap-1.5 rounded border border-copper/10 bg-obsidian/50 px-1.5 py-1"
                >
                  <div className="relative h-6 w-6 shrink-0 overflow-hidden rounded border border-copper/15 bg-obsidian">
                    {assets?.portrait ? (
                      <Image
                        src={assets.portrait}
                        alt=""
                        fill
                        className="object-cover object-top opacity-90"
                        sizes="24px"
                      />
                    ) : (
                      <span className="flex h-full w-full items-center justify-center text-[10px]">
                        {agent.icon}
                      </span>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1">
                      <span
                        className={cn(
                          "h-1.5 w-1.5 shrink-0 rounded-full",
                          STATUS_DOT[status],
                        )}
                      />
                      <p className="truncate font-title text-[9px] text-ivory">
                        {agent.name.split(" ")[0]}
                      </p>
                      <span className="ml-auto shrink-0 font-body text-[7px] text-titanium/45">
                        {STATUS_LABEL[status]}
                      </span>
                    </div>
                    {task ? (
                      <p className="truncate font-body text-[8px] text-copper/75">
                        {task}
                      </p>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ul>
          <p className="mt-1 text-center font-mono text-[7px] text-copper/45">
            {activeAgents} actifs · {BUREAU_AGENTS.length} total
          </p>
        </HudPanel>

        <HudPanel title="Journal">
          <ul className="max-h-28 space-y-0.5 overflow-y-auto font-mono text-[8px]">
            {displayLogs.length > 0 ? (
              displayLogs.slice(0, 6).map((log, i) => (
                <li
                  key={`${log.time}-${log.agent}-${i}`}
                  className="rounded border border-copper/5 bg-obsidian/40 px-1.5 py-0.5"
                >
                  <span className="text-copper/65">{log.time}</span>{" "}
                  <span className="text-ivory/75">{log.agent}</span>
                  <p className="truncate text-titanium/55">{log.message}</p>
                </li>
              ))
            ) : (
              <li className="py-2 text-center text-titanium/40">
                Aucune activité
              </li>
            )}
          </ul>
        </HudPanel>

        <HudPanel title="KPIs">
          <div className="grid grid-cols-2 gap-1.5">
            {metrics.map((m) => (
              <MetricCell
                key={m.label}
                label={m.label}
                value={m.value}
                live={m.live}
              />
            ))}
          </div>
        </HudPanel>
      </div>

      <div className="relative z-10 shrink-0 border-t border-copper/10 px-3 py-1.5">
        <div className="flex items-center gap-1.5 text-titanium/40">
          <Zap className="h-3 w-3 text-copper/40" />
          <p className="font-body text-[8px]">
            Clic bureau · Entrée pour ouvrir
          </p>
        </div>
      </div>
    </aside>
  );
}

function MetricCell({
  label,
  value,
  live = false,
}: {
  label: string;
  value: string;
  live?: boolean;
}) {
  return (
    <div className="rounded border border-copper/10 bg-obsidian/40 px-1.5 py-1">
      <p className="font-body text-[7px] uppercase tracking-wider text-copper/50">
        {label}
      </p>
      <p
        className={cn(
          "truncate font-mono text-[10px]",
          live ? "text-copper" : "text-ivory/80",
        )}
      >
        {value}
      </p>
    </div>
  );
}
