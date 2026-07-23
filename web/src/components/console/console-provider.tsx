"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import {
  fetchLobbyStats,
  getLobbyStatsCache,
  normalizeLobbyStats,
  type LobbyStats,
} from "@/lib/lobby-api";
import {
  countActiveAgents,
  fetchAgentsStatus,
  type AgentStatus,
  type AgentsStatusResponse,
} from "@/lib/openroom-api";
import { buildActivityFeed } from "@/lib/console/activity";
import { buildConsoleDepartments } from "@/lib/console/departments";
import {
  buildLiveDecisionsToday,
  buildLiveDeployments,
  buildLiveIncidents,
} from "@/lib/console/live-ops";
import {
  buildActivity24h,
  buildActivityHeatmap,
  buildDecisions7d,
  buildGlobalKpis,
  buildSystemMetrics,
} from "@/lib/console/rich-data";
import type { ConsoleActivityItem, ConsoleDepartment } from "@/lib/console/types";
import type { Metric } from "@/lib/console/rich-data-static";
import type { DeployStatus, Incident } from "@/lib/console/rich-data-static";

export const CONSOLE_POLL_MS = 12_000;
const LOBBY_STATS_POLL_MS = 30_000;

interface ConsoleContextValue {
  stats: LobbyStats;
  departments: ConsoleDepartment[];
  activityFeed: ConsoleActivityItem[];
  globalKpis: ReturnType<typeof buildGlobalKpis>;
  systemMetrics: Record<string, Metric>;
  activity24h: number[];
  activityHeatmap: number[][];
  decisions7d: { label: string; value: number }[];
  incidents: Incident[];
  deployments: Array<{
    id: string;
    service: string;
    version: string;
    by: string;
    time: string;
    status: DeployStatus;
  }>;
  decisionsToday: ReturnType<typeof buildLiveDecisionsToday>;
  activeAgents: number;
  totalAgents: number;
  liveAgents: Record<string, AgentStatus>;
  pipelineActive: boolean;
  codingPipeline?: AgentsStatusResponse["codingPipeline"];
  lastSyncedAt: Date | null;
  pollIntervalMs: number;
  refresh: () => void;
}

const ConsoleContext = createContext<ConsoleContextValue | null>(null);

const POLL_MS = CONSOLE_POLL_MS;

export function ConsoleProvider({ children }: { children: ReactNode }) {
  const [stats, setStats] = useState<LobbyStats>(normalizeLobbyStats(null));
  const [liveAgents, setLiveAgents] = useState<Record<string, AgentStatus>>({});
  const [activityFeed, setActivityFeed] = useState<ConsoleActivityItem[]>([]);
  const [pipelineActive, setPipelineActive] = useState(false);
  const [codingPipeline, setCodingPipeline] =
    useState<AgentsStatusResponse["codingPipeline"]>();
  const [lastSyncedAt, setLastSyncedAt] = useState<Date | null>(null);

  const refreshAgents = useCallback(() => {
    fetchAgentsStatus()
      .then((agentResult) => {
        if (agentResult.ok) {
          setLiveAgents(agentResult.data.agents);
          setPipelineActive(agentResult.data.pipelineActive);
          setCodingPipeline(agentResult.data.codingPipeline);
          setActivityFeed(buildActivityFeed(agentResult.data.recentLogs));
        }
        setLastSyncedAt(new Date());
      })
      .catch(() => undefined);
  }, []);

  const refreshLobbyStats = useCallback(() => {
    fetchLobbyStats()
      .then((lobbyStats) => setStats(normalizeLobbyStats(lobbyStats)))
      .catch(() => undefined);
  }, []);

  const refresh = useCallback(() => {
    refreshAgents();
    refreshLobbyStats();
  }, [refreshAgents, refreshLobbyStats]);

  useEffect(() => {
    const cached = getLobbyStatsCache();
    if (cached) setStats(normalizeLobbyStats(cached));
  }, []);

  useEffect(() => {
    refreshAgents();
    const agentsId = setInterval(refreshAgents, POLL_MS);

    let lobbyId: ReturnType<typeof setInterval> | undefined;
    const startLobbyPoll = () => {
      refreshLobbyStats();
      lobbyId = setInterval(refreshLobbyStats, LOBBY_STATS_POLL_MS);
    };

    let idleId: number | undefined;
    let lobbyTimeoutId: ReturnType<typeof setTimeout> | undefined;
    if (typeof requestIdleCallback !== "undefined") {
      idleId = requestIdleCallback(startLobbyPoll, { timeout: 3_000 });
    } else {
      lobbyTimeoutId = setTimeout(startLobbyPoll, 1_000);
    }

    return () => {
      clearInterval(agentsId);
      if (lobbyId) clearInterval(lobbyId);
      if (idleId !== undefined) cancelIdleCallback(idleId);
      if (lobbyTimeoutId) clearTimeout(lobbyTimeoutId);
    };
  }, [refreshAgents, refreshLobbyStats]);

  const departments = useMemo(
    () => buildConsoleDepartments(liveAgents, stats),
    [liveAgents, stats],
  );

  const totalAgents = useMemo(
    () => departments.reduce((n, d) => n + d.agents.length, 0),
    [departments],
  );

  const activeAgents = useMemo(() => countActiveAgents(liveAgents), [liveAgents]);

  const value = useMemo<ConsoleContextValue>(
    () => ({
      stats,
      departments,
      activityFeed,
      globalKpis: buildGlobalKpis(stats, activeAgents, totalAgents),
      systemMetrics: buildSystemMetrics(stats),
      activity24h: buildActivity24h(activityFeed),
      activityHeatmap: buildActivityHeatmap(activityFeed),
      decisions7d: buildDecisions7d(activityFeed),
      incidents: buildLiveIncidents(activityFeed, liveAgents, stats),
      deployments: buildLiveDeployments(activityFeed, codingPipeline),
      decisionsToday: buildLiveDecisionsToday(activityFeed),
      activeAgents,
      totalAgents,
      liveAgents,
      pipelineActive,
      codingPipeline,
      lastSyncedAt,
      pollIntervalMs: POLL_MS,
      refresh,
    }),
    [
      stats,
      departments,
      activityFeed,
      liveAgents,
      activeAgents,
      totalAgents,
      pipelineActive,
      codingPipeline,
      lastSyncedAt,
      refresh,
    ],
  );

  return (
    <ConsoleContext.Provider value={value}>{children}</ConsoleContext.Provider>
  );
}

export function useConsoleData(): ConsoleContextValue {
  const ctx = useContext(ConsoleContext);
  if (!ctx) {
    throw new Error("useConsoleData must be used within ConsoleProvider");
  }
  return ctx;
}

/** Returns console context when inside ConsoleShell, null otherwise. */
export function useOptionalConsoleData(): ConsoleContextValue | null {
  return useContext(ConsoleContext);
}
