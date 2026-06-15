"use client";

import Image from "next/image";
import Link from "next/link";
import { Activity, Crown, Radio, Zap } from "lucide-react";
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
import type { LobbyStats } from "@/lib/lobby-api";
import type {
  AgentStatus,
  AgentStatusKind,
  OpenRoomLogEntry,
} from "@/lib/openroom-api";
import {
  HudPanel,
  HudRingGauge,
  HudSparkline,
  HudWaveform,
} from "@/components/lobby/hq-monitor-charts";
import { cn } from "@/lib/utils";

interface HqActivityMonitorPanelProps {
  stats: LobbyStats;
  agents: Record<string, AgentStatus>;
  activeAgents: number;
  recentLogs: OpenRoomLogEntry[];
  pipelineActive: boolean;
  selectedOffice: HqSector | null;
  onSelectOffMap?: (access: HqOffMapAccess) => void;
}

const STATUS_LABEL: Record<AgentStatusKind, string> = {
  working: "Actif",
  waiting: "En attente",
  error: "Erreur",
  idle: "Repos",
};

const STATUS_DOT: Record<AgentStatusKind, string> = {
  working: "bg-emerald-400 shadow-[0_0_6px_rgba(52,211,153,0.6)]",
  waiting: "bg-copper animate-pulse shadow-[0_0_6px_rgba(192,138,98,0.6)]",
  error: "bg-red-500",
  idle: "bg-titanium/30",
};

function deriveSparkline(logs: OpenRoomLogEntry[]): number[] {
  const base = [2, 4, 3, 6, 5, 8, 4, 7, 9, 6, 8, 5];
  return base.map((v, i) => v + (logs.length > i % Math.max(logs.length, 1) ? 3 : 0));
}

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
  const names = new Set(sectorAgents.map((a) => a.name.split(" ")[0].toLowerCase()));
  const filtered = logs.filter(
    (log) =>
      ids.has(log.agent) ||
      names.has(log.agent.toLowerCase()) ||
      log.agent.toLowerCase().includes(office.id),
  );
  return filtered.length > 0 ? filtered : logs.slice(0, 8);
}

/** Right column — read-only activity monitoring (no links/buttons). */
export function HqActivityMonitorPanel({
  stats,
  agents,
  activeAgents,
  recentLogs,
  pipelineActive,
  selectedOffice,
  onSelectOffMap,
}: HqActivityMonitorPanelProps) {
  const totalAgents = BUREAU_AGENTS.length;
  const sectorAgents = agentsForOffice(selectedOffice);
  const displayLogs = logsForOffice(recentLogs, selectedOffice);
  const workingInSector = sectorAgents.filter(
    (a) => agents[a.id]?.status === "working",
  ).length;
  const badge = selectedOffice ? getOfficeBadge(selectedOffice, stats) : null;

  const sortedAgents = [...sectorAgents].sort((a, b) => {
    const order: Record<AgentStatusKind, number> = {
      working: 0,
      waiting: 1,
      error: 2,
      idle: 3,
    };
    const sa = agents[a.id]?.status ?? "idle";
    const sb = agents[b.id]?.status ?? "idle";
    return order[sa] - order[sb];
  });

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

      <div className="relative z-10 flex shrink-0 items-center gap-2 border-b border-copper/15 px-3 py-2.5">
        <Radio className="h-3.5 w-3.5 animate-pulse text-copper" />
        <span className="font-body text-[9px] uppercase tracking-[0.3em] text-copper">
          Activity Monitor
        </span>
        <span
          className={cn(
            "ml-auto rounded px-1.5 py-0.5 font-mono text-[7px] uppercase",
            pipelineActive
              ? "bg-emerald-500/15 text-emerald-400"
              : "bg-copper/10 text-titanium/50",
          )}
        >
          {pipelineActive ? "Pipeline ON" : "Standby"}
        </span>
      </div>

      <div className="relative z-10 flex min-h-0 flex-1 flex-col gap-1.5 overflow-y-auto p-2">
        <HudPanel title="Accès rapide">
          <Link
            href={HQ_CEO_ACCESS.href}
            className="flex items-center gap-2 rounded-lg border border-copper/25 bg-copper/5 px-2 py-2 transition hover:border-copper/40 hover:bg-copper/10"
          >
            <div className="relative h-9 w-9 shrink-0 overflow-hidden rounded-md border border-copper/20 bg-obsidian">
              <Image
                src={HQ_CEO_ACCESS.portrait ?? ""}
                alt=""
                fill
                className="object-cover object-top"
                sizes="36px"
              />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center gap-1">
                <Crown className="h-3 w-3 text-copper" />
                <p className="truncate font-title text-[11px] font-medium text-ivory">
                  {HQ_CEO_ACCESS.title}
                </p>
              </div>
              <p className="truncate font-body text-[9px] text-titanium/65">
                {HQ_CEO_ACCESS.subtitle}
              </p>
            </div>
            {stats.ceoNotifications > 0 ? (
              <span className="shrink-0 rounded-full bg-copper px-1.5 py-0.5 font-mono text-[8px] text-obsidian">
                {stats.ceoNotifications}
              </span>
            ) : null}
          </Link>
        </HudPanel>

        {HQ_OFF_MAP_ACCESS.length > 0 ? (
          <HudPanel title="Hors plan — accès directs">
            <ul className="space-y-1.5">
              {HQ_OFF_MAP_ACCESS.map((access) => {
                const isSelected = selectedOffice?.id === access.id;
                const accessBadge = getOfficeBadge(access, stats);

                return (
                  <li key={access.id}>
                    <button
                      type="button"
                      onClick={() => onSelectOffMap?.(access)}
                      className={cn(
                        "flex w-full items-center gap-2 rounded-lg border px-2 py-2 text-left transition",
                        isSelected
                          ? "border-copper/50 bg-copper/15"
                          : "border-copper/20 bg-copper/5 hover:border-copper/35 hover:bg-copper/10",
                      )}
                    >
                      {access.portrait ? (
                        <div className="relative h-9 w-9 shrink-0 overflow-hidden rounded-md border border-copper/20 bg-obsidian">
                          <Image
                            src={access.portrait}
                            alt=""
                            fill
                            className="object-cover object-top"
                            sizes="36px"
                          />
                        </div>
                      ) : (
                        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md border border-copper/20 bg-obsidian text-lg">
                          {access.icon}
                        </span>
                      )}
                      <div className="min-w-0 flex-1">
                        <p className="truncate font-title text-[11px] font-medium text-ivory">
                          {access.number}. {access.title}
                        </p>
                        <p className="truncate font-body text-[9px] text-titanium/65">
                          {access.subtitle}
                        </p>
                      </div>
                      {accessBadge.highlight ? (
                        <span className="shrink-0 rounded-full bg-copper px-1.5 py-0.5 font-mono text-[8px] text-obsidian">
                          {accessBadge.label}
                        </span>
                      ) : null}
                    </button>
                  </li>
                );
              })}
            </ul>
          </HudPanel>
        ) : null}

        {selectedOffice ? (
          <HudPanel title="Secteur sélectionné">
            <div className="flex items-start gap-2">
              <span className="text-xl leading-none">{selectedOffice.icon}</span>
              <div className="min-w-0 flex-1">
                <p className="truncate font-title text-xs font-medium text-ivory">
                  {selectedOffice.title}
                </p>
                <p className="truncate font-body text-[10px] text-titanium/70">
                  {selectedOffice.subtitle}
                </p>
                {badge ? (
                  <p
                    className={cn(
                      "mt-1 inline-block rounded px-1.5 py-0.5 font-body text-[9px]",
                      badge.highlight
                        ? "bg-copper/20 text-copper"
                        : "bg-white/5 text-titanium",
                    )}
                  >
                    {badge.label}
                  </p>
                ) : null}
              </div>
            </div>
          </HudPanel>
        ) : (
          <HudPanel title="Vue globale">
            <p className="font-body text-[10px] leading-relaxed text-titanium/70">
              Flux temps réel — tous les bureaux. Cliquez un secteur sur la carte
              pour filtrer.
            </p>
          </HudPanel>
        )}

        <div className="grid grid-cols-2 gap-1.5">
          <HudPanel title="Charge">
            <HudSparkline data={deriveSparkline(displayLogs)} />
          </HudPanel>
          <HudPanel title="Secteur" className="flex items-center justify-center">
            <HudRingGauge
              value={workingInSector}
              max={Math.max(sectorAgents.length, 1)}
              label="actifs"
            />
          </HudPanel>
        </div>

        <HudPanel title="Flux neural">
          <HudWaveform />
          <div className="mt-1 flex justify-between font-mono text-[7px] text-copper/50">
            <span>GLOBAL {activeAgents}</span>
            <span>TOTAL {totalAgents}</span>
            <span>LOGS {displayLogs.length}</span>
          </div>
        </HudPanel>

        <HudPanel title="Agents — statut live" className="min-h-0 flex-1">
          <ul className="max-h-44 space-y-1.5 overflow-y-auto pr-0.5">
            {sortedAgents.map((agent) => {
              const status = agents[agent.id]?.status ?? "idle";
              const task = agents[agent.id]?.currentTask;
              const assets = getAgentOfficeAssets(agent.id);
              const progress = agents[agent.id]?.progress;

              return (
                <li
                  key={agent.id}
                  className="flex items-start gap-2 rounded border border-copper/10 bg-obsidian/50 px-2 py-1.5"
                >
                  <div className="relative mt-0.5 h-7 w-7 shrink-0 overflow-hidden rounded border border-copper/15 bg-obsidian">
                    {assets?.portrait ? (
                      <Image
                        src={assets.portrait}
                        alt=""
                        fill
                        className="object-cover object-top opacity-90"
                        sizes="28px"
                      />
                    ) : (
                      <span className="flex h-full w-full items-center justify-center text-xs">
                        {agent.icon}
                      </span>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-1.5">
                      <span
                        className={cn("h-1.5 w-1.5 shrink-0 rounded-full", STATUS_DOT[status])}
                      />
                      <p className="truncate font-title text-[10px] text-ivory">
                        {agent.name}
                      </p>
                      <span className="ml-auto shrink-0 font-body text-[8px] text-titanium/50">
                        {STATUS_LABEL[status]}
                      </span>
                    </div>
                    <p className="truncate font-body text-[9px] text-titanium/50">
                      {agent.role}
                    </p>
                    {task ? (
                      <p className="mt-0.5 line-clamp-2 font-body text-[9px] text-copper/80">
                        {task}
                      </p>
                    ) : null}
                    {typeof progress === "number" ? (
                      <div className="mt-1 h-1 overflow-hidden rounded-sm bg-copper/10">
                        <div
                          className="h-full rounded-sm bg-copper/70"
                          style={{ width: `${Math.min(100, progress)}%` }}
                        />
                      </div>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ul>
        </HudPanel>

        <HudPanel title="Journal activité">
          <div className="flex items-center gap-1.5 pb-1">
            <Activity className="h-2.5 w-2.5 text-copper/60" />
            <span className="font-body text-[8px] text-titanium/40">
              {displayLogs.length} entrées
              {selectedOffice ? ` · ${selectedOffice.shortcutLabel}` : ""}
            </span>
          </div>
          <ul className="max-h-36 space-y-1 overflow-y-auto font-mono text-[8px]">
            {displayLogs.length > 0 ? (
              displayLogs.map((log, i) => (
                <li
                  key={`${log.time}-${log.agent}-${i}`}
                  className="rounded border border-copper/5 bg-obsidian/40 px-1.5 py-1"
                >
                  <span className="text-copper/70">{log.time}</span>{" "}
                  <span className="text-ivory/80">{log.agent}</span>
                  <p className="mt-0.5 text-titanium/60">{log.message}</p>
                </li>
              ))
            ) : (
              <li className="py-2 text-center text-titanium/40">
                Aucune activité récente
              </li>
            )}
          </ul>
        </HudPanel>

        <HudPanel title="Métriques secteur">
          <div className="grid grid-cols-2 gap-2">
            <MetricCell
              label="API"
              value={stats.apiOnline ? "Online" : "Offline"}
              live={stats.apiOnline}
            />
            <MetricCell
              label="PR Hub"
              value={String(stats.hubPrCount)}
              live={stats.hubPrCount > 0}
            />
            <MetricCell
              label="Tickets"
              value={String(stats.appOpenTickets)}
              live={stats.appOpenTickets > 0}
            />
            <MetricCell
              label="Posts"
              value={String(stats.marketingPendingPosts)}
              live={stats.marketingPendingPosts > 0}
            />
            <MetricCell label="R&D" value={String(stats.rdSessions)} />
            <MetricCell label="Apps" value={String(stats.connectedApps)} />
          </div>
        </HudPanel>
      </div>

      <div className="relative z-10 shrink-0 border-t border-copper/10 px-3 py-2">
        <div className="flex items-center gap-1.5 text-titanium/40">
          <Zap className="h-3 w-3 text-copper/40" />
          <p className="font-body text-[9px]">
            Double-clic sur la carte pour entrer dans un bureau
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
    <div className="rounded border border-copper/10 bg-obsidian/40 px-2 py-1.5">
      <p className="font-body text-[7px] uppercase tracking-wider text-copper/50">
        {label}
      </p>
      <p
        className={cn(
          "font-mono text-[10px]",
          live ? "text-copper" : "text-ivory/80",
        )}
      >
        {value}
      </p>
    </div>
  );
}
