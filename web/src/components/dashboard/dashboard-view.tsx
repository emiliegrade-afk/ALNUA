"use client";

import { useCallback, useEffect, useState } from "react";
import { BriefingCard } from "@/components/dashboard/briefing-card";
import { ProjectCards } from "@/components/dashboard/project-cards";
import { COOChat } from "@/components/dashboard/coo-chat";
import { AgentFeed } from "@/components/dashboard/agent-feed";
import { HubHeader } from "@/components/layout/hub-header";
import {
  checkApiHealth,
  fetchBriefing,
  fetchProjects,
  fetchTickets,
} from "@/lib/api";
import { fetchAgentLogs } from "@/lib/supabase";
import type { AgentLog, ProjectWithStats } from "@/lib/types";

export function DashboardView() {
  const [briefing, setBriefing] = useState<string | null>(null);
  const [briefingLoading, setBriefingLoading] = useState(true);
  const [briefingError, setBriefingError] = useState<string | null>(null);
  const [projects, setProjects] = useState<ProjectWithStats[]>([]);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [logs, setLogs] = useState<AgentLog[]>([]);
  const [logsLoading, setLogsLoading] = useState(true);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const loadBriefing = useCallback(async () => {
    setBriefingLoading(true);
    setBriefingError(null);
    try {
      const text = await fetchBriefing();
      setBriefing(text);
    } catch (err) {
      setBriefing(null);
      setBriefingError(
        err instanceof Error ? err.message : "Impossible de charger le briefing."
      );
    } finally {
      setBriefingLoading(false);
    }
  }, []);

  const loadProjects = useCallback(async () => {
    setProjectsLoading(true);
    try {
      const rawProjects = await fetchProjects();
      const withStats: ProjectWithStats[] = await Promise.all(
        rawProjects.map(async (project) => {
          try {
            const open = await fetchTickets(project.id, "open");
            const critical = open.filter(
              (t) => t.priority === "critical" || t.priority === "high"
            ).length;
            return {
              ...project,
              openTickets: open.length,
              criticalTickets: critical,
            };
          } catch {
            return { ...project, openTickets: 0, criticalTickets: 0 };
          }
        })
      );
      setProjects(withStats);
    } catch {
      setProjects([]);
    } finally {
      setProjectsLoading(false);
    }
  }, []);

  const loadLogs = useCallback(async () => {
    setLogsLoading(true);
    try {
      const data = await fetchAgentLogs(25);
      setLogs(data);
    } catch {
      setLogs([]);
    } finally {
      setLogsLoading(false);
    }
  }, []);

  const refreshAll = useCallback(async () => {
    setRefreshing(true);
    const online = await checkApiHealth();
    setApiOnline(online);
    await Promise.all([loadBriefing(), loadProjects(), loadLogs()]);
    setRefreshing(false);
  }, [loadBriefing, loadProjects, loadLogs]);

  useEffect(() => {
    refreshAll();
    const interval = setInterval(loadLogs, 30_000);
    return () => clearInterval(interval);
  }, [refreshAll, loadLogs]);

  return (
    <div className="space-y-8">
      <HubHeader
        apiOnline={apiOnline}
        onRefresh={refreshAll}
        refreshing={refreshing}
      />

      <BriefingCard
        briefing={briefing}
        loading={briefingLoading}
        error={briefingError}
        onRefresh={loadBriefing}
      />

      <section>
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-sm font-medium uppercase tracking-widest text-titanium">
            Projets actifs
          </h2>
          <span className="text-xs text-titanium/60">
            {projects.length} branches
          </span>
        </div>
        <ProjectCards projects={projects} loading={projectsLoading} />
      </section>

      <section className="grid min-h-[520px] gap-6 lg:grid-cols-5 lg:items-stretch">
        <div className="flex min-h-[480px] flex-col lg:col-span-3">
          <COOChat />
        </div>
        <div className="lg:col-span-2">
          <AgentFeed logs={logs} loading={logsLoading} />
        </div>
      </section>
    </div>
  );
}
