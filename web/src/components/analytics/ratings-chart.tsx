"use client";

import { useMemo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { ChartEmptyState } from "@/components/analytics/chart-empty-state";
import { getProjectChartColor } from "@/components/analytics/analytics.constants";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { FeedbackRow } from "@/lib/analytics";
import type { Project } from "@/lib/types";
import { Star } from "lucide-react";

interface RatingsChartProps {
  feedback: FeedbackRow[];
  projects: Project[];
  projectFilter: string;
}

function buildRatingData(
  feedback: FeedbackRow[],
  projects: Project[],
  projectFilter: string
) {
  const rated = feedback.filter((f) => f.rating != null);
  const targetProjects =
    projectFilter === "all"
      ? projects
      : projects.filter((p) => p.id === projectFilter);

  const rows: {
    projectId: string;
    projectName: string;
    star: number;
    count: number;
    color: string;
    avg: number;
    label: string;
  }[] = [];

  for (const project of targetProjects) {
    const projectFeedback = rated.filter((f) => f.project_id === project.id);
    const color = getProjectChartColor(project);
    const avg =
      projectFeedback.length > 0
        ? projectFeedback.reduce((s, f) => s + (f.rating ?? 0), 0) /
          projectFeedback.length
        : 0;

    for (let star = 1; star <= 5; star++) {
      const count = projectFeedback.filter((f) => f.rating === star).length;
      rows.push({
        projectId: project.id,
        projectName: project.name,
        star,
        count,
        color,
        avg,
        label: `${project.name} · ${star}★`,
      });
    }
  }

  return rows;
}

function AverageBadge({ avg }: { avg: number }) {
  if (!avg) {
    return <span className="text-sm text-titanium/50">–</span>;
  }
  return (
    <span className="flex items-center gap-1 text-sm font-medium text-ivory">
      {avg.toFixed(1)}
      <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
    </span>
  );
}

export function RatingsChart({
  feedback,
  projects,
  projectFilter,
}: RatingsChartProps) {
  const data = useMemo(
    () => buildRatingData(feedback, projects, projectFilter),
    [feedback, projects, projectFilter]
  );

  const hasRatings = feedback.some((f) => f.rating != null);

  const projectAvgs = useMemo(() => {
    const map = new Map<string, number>();
    for (const row of data) {
      if (!map.has(row.projectId)) map.set(row.projectId, row.avg);
    }
    return map;
  }, [data]);

  const chartHeight = Math.max(200, data.length * 28);

  return (
    <Card className="border-copper/10 bg-surface/80">
      <CardHeader className="pb-2">
        <div className="flex items-start justify-between gap-4">
          <CardTitle className="text-sm font-medium text-ivory">
            Avis &amp; Notes
          </CardTitle>
          {projectFilter !== "all" && (
            <AverageBadge avg={projectAvgs.get(projectFilter) ?? 0} />
          )}
        </div>
      </CardHeader>
      <CardContent>
        {!hasRatings ? (
          <ChartEmptyState compact />
        ) : (
          <div className="flex gap-4">
            <ResponsiveContainer width="100%" height={chartHeight}>
              <BarChart
                data={data}
                layout="vertical"
                margin={{ top: 4, right: 8, left: 4, bottom: 4 }}
              >
                <CartesianGrid stroke="#ffffff10" horizontal={false} />
                <XAxis
                  type="number"
                  tick={{ fill: "#9ca3af", fontSize: 11 }}
                  axisLine={{ stroke: "#ffffff15" }}
                  tickLine={false}
                  allowDecimals={false}
                />
                <YAxis
                  type="category"
                  dataKey="label"
                  tick={{ fill: "#9ca3af", fontSize: 10 }}
                  axisLine={{ stroke: "#ffffff15" }}
                  tickLine={false}
                  width={100}
                />
                <Tooltip
                  contentStyle={{
                    background: "#141414",
                    border: "1px solid rgba(192,138,114,0.25)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="count" name="Avis" radius={[0, 4, 4, 0]} maxBarSize={18}>
                  {data.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} fillOpacity={0.85} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>

            {projectFilter === "all" && (
              <div className="hidden shrink-0 flex-col gap-2 border-l border-copper/10 pl-4 sm:flex">
                <p className="text-[10px] uppercase tracking-wider text-titanium/60">
                  Moyenne
                </p>
                {projects.map((p) => (
                  <div key={p.id} className="flex items-center justify-between gap-3">
                    <span className="max-w-[80px] truncate text-xs text-titanium">
                      {p.name}
                    </span>
                    <AverageBadge avg={projectAvgs.get(p.id) ?? 0} />
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
