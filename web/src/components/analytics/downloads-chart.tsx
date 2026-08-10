"use client";

import { useMemo } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartEmptyState } from "@/components/analytics/chart-empty-state";
import {
  CHART_COLORS,
  formatChartDate,
  getProjectChartColor,
} from "@/components/analytics/analytics.constants";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AnalyticsRow } from "@/lib/analytics";
import type { Project } from "@/lib/types";

interface DownloadsChartProps {
  rows: AnalyticsRow[];
  projects: Project[];
  projectFilter: string;
  onAddMetric?: () => void;
}

function buildChartData(
  rows: AnalyticsRow[],
  projects: Project[],
  projectFilter: string
) {
  const relevantProjects =
    projectFilter === "all"
      ? projects
      : projects.filter((p) => p.id === projectFilter);

  const dates = new Set<string>();
  for (const row of rows) {
    if (row.metric_name === "downloads" || row.metric_name === "subscriptions") {
      dates.add(row.date.slice(0, 10));
    }
  }
  const sortedDates = Array.from(dates).sort();

  if (projectFilter !== "all") {
    return sortedDates.map((date) => {
      const point: Record<string, string | number> = { date, label: formatChartDate(date) };
      const dl = rows.find(
        (r) =>
          r.date.slice(0, 10) === date &&
          r.metric_name === "downloads" &&
          r.project_id === projectFilter
      );
      const sub = rows.find(
        (r) =>
          r.date.slice(0, 10) === date &&
          r.metric_name === "subscriptions" &&
          r.project_id === projectFilter
      );
      point.downloads = dl ? Number(dl.value) : 0;
      point.subscriptions = sub ? Number(sub.value) : 0;
      return point;
    });
  }

  return sortedDates.map((date) => {
    const point: Record<string, string | number> = { date, label: formatChartDate(date) };
    for (const project of relevantProjects) {
      const dl = rows.filter(
        (r) =>
          r.date.slice(0, 10) === date &&
          r.metric_name === "downloads" &&
          r.project_id === project.id
      );
      const sub = rows.filter(
        (r) =>
          r.date.slice(0, 10) === date &&
          r.metric_name === "subscriptions" &&
          r.project_id === project.id
      );
      point[`${project.id}_downloads`] = dl.length
        ? dl.reduce((s, r) => s + Number(r.value), 0)
        : 0;
      point[`${project.id}_subscriptions`] = sub.length
        ? sub[sub.length - 1]
          ? Number(sub[sub.length - 1].value)
          : 0
        : 0;
    }
    return point;
  });
}

function hasDownloadData(rows: AnalyticsRow[]): boolean {
  return rows.some(
    (r) => r.metric_name === "downloads" || r.metric_name === "subscriptions"
  );
}

export function DownloadsChart({
  rows,
  projects,
  projectFilter,
  onAddMetric,
}: DownloadsChartProps) {
  const data = useMemo(
    () => buildChartData(rows, projects, projectFilter),
    [rows, projects, projectFilter]
  );

  const empty = !hasDownloadData(rows);

  const singleProject =
    projectFilter !== "all"
      ? projects.find((p) => p.id === projectFilter)
      : null;
  const singleColor = singleProject
    ? getProjectChartColor(singleProject)
    : CHART_COLORS.copper;

  return (
    <Card className="border-copper/10 bg-surface/80">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-ivory">
          Téléchargements &amp; Abonnements
        </CardTitle>
      </CardHeader>
      <CardContent>
        {empty ? (
          <ChartEmptyState onAddMetric={onAddMetric} />
        ) : (
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
              <CartesianGrid stroke="#ffffff10" strokeDasharray="3 3" />
              <XAxis
                dataKey="label"
                tick={{ fill: "#9ca3af", fontSize: 11 }}
                axisLine={{ stroke: "#ffffff15" }}
                tickLine={false}
              />
              <YAxis
                tick={{ fill: "#9ca3af", fontSize: 11 }}
                axisLine={{ stroke: "#ffffff15" }}
                tickLine={false}
                width={48}
              />
              <Tooltip
                contentStyle={{
                  background: "#141414",
                  border: "1px solid rgba(224,155,106,0.25)",
                  borderRadius: 8,
                  fontSize: 12,
                }}
                labelStyle={{ color: "#e8e4df" }}
              />
              <Legend wrapperStyle={{ fontSize: 11, paddingTop: 12 }} />

              {projectFilter !== "all" ? (
                <>
                  <Line
                    type="monotone"
                    dataKey="downloads"
                    name="Téléchargements"
                    stroke={singleColor}
                    strokeWidth={2}
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                  <Line
                    type="monotone"
                    dataKey="subscriptions"
                    name="Abonnements"
                    stroke={singleColor}
                    strokeWidth={2}
                    strokeDasharray="5 5"
                    dot={false}
                    activeDot={{ r: 4 }}
                  />
                </>
              ) : (
                projects.flatMap((project) => {
                  const color = getProjectChartColor(project);
                  return [
                    <Line
                      key={`${project.id}_dl`}
                      type="monotone"
                      dataKey={`${project.id}_downloads`}
                      name={`${project.name} — dl`}
                      stroke={color}
                      strokeWidth={2}
                      dot={false}
                      connectNulls
                    />,
                    <Line
                      key={`${project.id}_sub`}
                      type="monotone"
                      dataKey={`${project.id}_subscriptions`}
                      name={`${project.name} — abo`}
                      stroke={color}
                      strokeWidth={1.5}
                      strokeDasharray="4 4"
                      dot={false}
                      connectNulls
                    />,
                  ];
                })
              )}
            </LineChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}
