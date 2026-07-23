"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import {
  ChevronDown,
  ChevronRight,
  ExternalLink,
  AlertTriangle,
} from "lucide-react";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  formatChartDate,
  getProjectChartColor,
  isActiveProject,
} from "@/components/analytics/analytics.constants";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import type { AnalyticsRow } from "@/lib/analytics";
import { getProjectAccent } from "@/lib/projects";
import type { Project } from "@/lib/types";
import type { TicketWithProject } from "@/lib/tickets";
import { ROUTES } from "@/lib/routes";
import { cn } from "@/lib/utils";

interface ProjectAccordionProps {
  projects: Project[];
  analyticsRows: AnalyticsRow[];
  tickets: TicketWithProject[];
}

function ProjectSection({
  project,
  downloadRows,
  latestMrr,
  latestSubs,
  criticalTickets,
  defaultOpen,
}: {
  project: Project;
  downloadRows: AnalyticsRow[];
  latestMrr: number | null;
  latestSubs: number | null;
  criticalTickets: TicketWithProject[];
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen ?? false);
  const accent = getProjectAccent(project.branch);
  const color = getProjectChartColor(project);

  const chartData = useMemo(() => {
    const byDate = new Map<string, number>();
    for (const row of downloadRows) {
      const d = row.date.slice(0, 10);
      byDate.set(d, (byDate.get(d) ?? 0) + Number(row.value));
    }
    return Array.from(byDate.entries())
      .sort(([a], [b]) => a.localeCompare(b))
      .map(([date, value]) => ({
        date,
        label: formatChartDate(date),
        downloads: value,
      }));
  }, [downloadRows]);

  return (
    <Card className={cn("border-white/[0.06] bg-surface/60", accent.border)}>
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-3 px-4 py-3 text-left"
      >
        {open ? (
          <ChevronDown className="h-4 w-4 shrink-0 text-titanium" />
        ) : (
          <ChevronRight className="h-4 w-4 shrink-0 text-titanium" />
        )}
        <span className={cn("h-2 w-2 shrink-0 rounded-full", accent.dot)} />
        <span className="flex-1 font-medium text-ivory">{project.name}</span>
        <span className="text-xs text-titanium">
          {latestSubs != null ? `${latestSubs} abo` : "– abo"}
          {" · "}
          {latestMrr != null
            ? `${new Intl.NumberFormat("fr-FR", { style: "currency", currency: "EUR", maximumFractionDigits: 0 }).format(latestMrr)} MRR`
            : "– MRR"}
        </span>
      </button>

      {open && (
        <CardContent className="border-t border-white/[0.06] pt-4">
          <div className="grid gap-4 lg:grid-cols-2">
            <div>
              <p className="mb-2 text-[11px] uppercase tracking-wider text-titanium/60">
                Téléchargements — 30 jours
              </p>
              {chartData.length === 0 ? (
                <p className="py-8 text-center text-sm text-titanium/50">
                  Pas de données downloads
                </p>
              ) : (
                <ResponsiveContainer width="100%" height={140}>
                  <LineChart data={chartData}>
                    <CartesianGrid stroke="#ffffff08" strokeDasharray="3 3" />
                    <XAxis
                      dataKey="label"
                      tick={{ fill: "#9ca3af", fontSize: 10 }}
                      axisLine={false}
                      tickLine={false}
                    />
                    <YAxis
                      tick={{ fill: "#9ca3af", fontSize: 10 }}
                      axisLine={false}
                      tickLine={false}
                      width={36}
                    />
                    <Tooltip
                      contentStyle={{
                        background: "#141414",
                        border: "1px solid rgba(192,138,114,0.25)",
                        borderRadius: 8,
                        fontSize: 11,
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="downloads"
                      stroke={color}
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>

            <div>
              <p className="mb-2 text-[11px] uppercase tracking-wider text-titanium/60">
                Tickets critiques ouverts
              </p>
              {criticalTickets.length === 0 ? (
                <p className="py-4 text-sm text-titanium/50">
                  Aucun ticket critique ouvert
                </p>
              ) : (
                <ul className="space-y-2">
                  {criticalTickets.map((t) => (
                    <li
                      key={t.id}
                      className="flex items-start gap-2 rounded-lg border border-white/[0.06] bg-obsidian/40 px-3 py-2"
                    >
                      <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0 text-red-400" />
                      <span className="line-clamp-2 text-sm text-ivory/90">
                        {t.title}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              <Button
                asChild
                variant="outline"
                size="sm"
                className="mt-3 border-copper/25 text-copper-glow hover:bg-copper/10"
              >
                <Link href={`${ROUTES.tickets}?project=${project.id}`}>
                  Voir les tickets
                  <ExternalLink className="ml-1.5 h-3 w-3" />
                </Link>
              </Button>
            </div>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

function latestMetric(
  rows: AnalyticsRow[],
  projectId: string,
  metricName: string
): number | null {
  const filtered = rows
    .filter(
      (r) => r.project_id === projectId && r.metric_name === metricName
    )
    .sort((a, b) => b.date.localeCompare(a.date));
  return filtered.length ? Number(filtered[0].value) : null;
}

export function ProjectAccordion({
  projects,
  analyticsRows,
  tickets,
}: ProjectAccordionProps) {
  const activeProjects = projects.filter(isActiveProject);

  if (activeProjects.length === 0) {
    return null;
  }

  return (
    <section className="space-y-3">
      <div>
        <h2 className="text-sm font-medium text-ivory">Par projet</h2>
        <p className="text-xs text-titanium">
          Vue détaillée par app — downloads, MRR et tickets critiques.
        </p>
      </div>
      <div className="space-y-2">
        {activeProjects.map((project, i) => {
          const downloadRows = analyticsRows.filter(
            (r) =>
              r.project_id === project.id && r.metric_name === "downloads"
          );
          const criticalTickets = tickets
            .filter(
              (t) =>
                t.project_id === project.id &&
                t.priority === "critical" &&
                t.status === "open"
            )
            .slice(0, 3);

          return (
            <ProjectSection
              key={project.id}
              project={project}
              downloadRows={downloadRows}
              latestMrr={latestMetric(analyticsRows, project.id, "mrr")}
              latestSubs={latestMetric(analyticsRows, project.id, "subscriptions")}
              criticalTickets={criticalTickets}
              defaultOpen={i === 0}
            />
          );
        })}
      </div>
    </section>
  );
}
