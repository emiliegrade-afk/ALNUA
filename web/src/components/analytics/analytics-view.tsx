"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Plus } from "lucide-react";
import { AddMetricModal } from "@/components/analytics/add-metric-modal";
import { AnalyticsFilters } from "@/components/analytics/analytics-filters";
import { AnalyticsChartsSection } from "@/components/analytics/analytics-charts";
import { AnalyticsKpiCards } from "@/components/analytics/analytics-kpi-cards";
import { Button } from "@/components/ui/button";
import { fetchProjects } from "@/lib/api";
import {
  fetchAnalytics,
  fetchAnalyticsRevenue,
  fetchAnalyticsSummary,
  fetchFeedback,
  type AnalyticsPeriod,
  type AnalyticsRow,
  type AnalyticsSummary,
  type FeedbackRow,
  type RevenueMonth,
} from "@/lib/analytics";
import { fetchTicketsList, type TicketWithProject } from "@/lib/tickets";
import type { Project } from "@/lib/types";

export function AnalyticsView() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [period, setPeriod] = useState<AnalyticsPeriod>("30d");
  const [projectFilter, setProjectFilter] = useState("all");

  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [analyticsRows, setAnalyticsRows] = useState<AnalyticsRow[]>([]);
  const [revenueMonths, setRevenueMonths] = useState<RevenueMonth[]>([]);
  const [feedback, setFeedback] = useState<FeedbackRow[]>([]);
  const [tickets, setTickets] = useState<TicketWithProject[]>([]);

  const [loading, setLoading] = useState(true);
  const [metricModalOpen, setMetricModalOpen] = useState(false);

  const projectIdParam = projectFilter === "all" ? undefined : projectFilter;

  const loadData = useCallback(async () => {
    setLoading(true);
    try {
      const [summaryData, rows, revenue, fb, tk] = await Promise.all([
        fetchAnalyticsSummary(projectIdParam),
        fetchAnalytics({ project_id: projectIdParam, period }),
        fetchAnalyticsRevenue({ project_id: projectIdParam, period }),
        fetchFeedback({ limit: 50 }),
        fetchTicketsList({ limit: 100 }),
      ]);
      setSummary(summaryData);
      setAnalyticsRows(rows);
      setRevenueMonths(revenue.months ?? []);
      setFeedback(fb);
      setTickets(tk);
    } catch {
      setSummary(null);
      setAnalyticsRows([]);
      setRevenueMonths([]);
      setFeedback([]);
      setTickets([]);
    } finally {
      setLoading(false);
    }
  }, [period, projectIdParam]);

  useEffect(() => {
    fetchProjects().then(setProjects).catch(() => setProjects([]));
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const hasAnyAnalytics = analyticsRows.length > 0;

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="forge-heading text-[11px] text-copper/80">Pilotage</p>
          <p className="mt-1 text-sm text-titanium">
            Téléchargements, abonnements, revenus et avis — tous tes projets en
            un coup d&apos;œil.
          </p>
        </div>
        <Button
          onClick={() => setMetricModalOpen(true)}
          className="shrink-0 bg-copper hover:bg-copper-glow"
        >
          <Plus className="mr-2 h-4 w-4" />
          Saisir une métrique
        </Button>
      </header>

      <AnalyticsKpiCards summary={summary} loading={loading} />

      <AnalyticsFilters
        period={period}
        onPeriodChange={setPeriod}
        projectFilter={projectFilter}
        onProjectFilterChange={setProjectFilter}
        projects={projects}
      />

      {loading ? (
        <div className="flex min-h-[320px] items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-copper/60" />
        </div>
      ) : (
        <>
          <AnalyticsChartsSection
            analyticsRows={analyticsRows}
            projects={projects}
            projectFilter={projectFilter}
            revenueMonths={revenueMonths}
            feedback={feedback}
            tickets={tickets}
            onAddMetric={() => setMetricModalOpen(true)}
          />

          {!hasAnyAnalytics && (
            <p className="text-center text-xs text-titanium/50">
              Les KPI et graphiques s&apos;actualiseront dès que des métriques
              seront disponibles.
            </p>
          )}
        </>
      )}

      <AddMetricModal
        open={metricModalOpen}
        onOpenChange={setMetricModalOpen}
        projects={projects}
        onCreated={loadData}
        defaultProjectId={projectFilter !== "all" ? projectFilter : undefined}
      />
    </div>
  );
}
