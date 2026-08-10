"use client";

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
import { format, parseISO } from "date-fns";
import { fr } from "date-fns/locale";
import { BETA_TYPE_LABELS } from "@/components/beta/beta.constants";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { BetaStats } from "@/lib/beta-api";

const TYPE_COLORS = ["#E09B6A", "#22c55e", "#f59e0b", "#06b6d4"];
const SEV_COLORS: Record<string, string> = {
  bloquant: "#ef4444",
  majeur: "#f97316",
  mineur: "#eab308",
  cosmétique: "#94a3b8",
  non_renseigné: "#64748b",
};

interface BetaStatsChartsProps {
  stats: BetaStats;
}

export function BetaStatsCharts({ stats }: BetaStatsChartsProps) {
  const typeData = Object.entries(stats.by_type).map(([type, count]) => ({
    name: BETA_TYPE_LABELS[type] ?? type,
    count,
  }));

  const severityData = Object.entries(stats.by_severity).map(([sev, count]) => ({
    name: sev,
    count,
    fill: SEV_COLORS[sev] ?? "#E09B6A",
  }));

  const timelineData = stats.timeline_7d.map((d) => ({
    ...d,
    label: format(parseISO(d.date), "EEE d", { locale: fr }),
  }));

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card className="border-copper/15 bg-surface/80">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-ivory">
            Feedbacks par type
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={typeData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="name" tick={{ fill: "#A7ADB5", fontSize: 11 }} />
              <YAxis tick={{ fill: "#A7ADB5", fontSize: 11 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  background: "#14171D",
                  border: "1px solid rgba(255,255,255,0.1)",
                  borderRadius: 8,
                }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {typeData.map((_, i) => (
                  <Cell key={i} fill={TYPE_COLORS[i % TYPE_COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card className="border-copper/15 bg-surface/80">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-ivory">
            Feedbacks par sévérité
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={severityData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="name" tick={{ fill: "#A7ADB5", fontSize: 11 }} />
              <YAxis tick={{ fill: "#A7ADB5", fontSize: 11 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  background: "#14171D",
                  border: "1px solid rgba(255,255,255,0.1)",
                  borderRadius: 8,
                }}
              />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {severityData.map((entry) => (
                  <Cell key={entry.name} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <Card className="border-copper/15 bg-surface/80 lg:col-span-2">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-ivory">
            Timeline — 7 derniers jours
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={timelineData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
              <XAxis dataKey="label" tick={{ fill: "#A7ADB5", fontSize: 11 }} />
              <YAxis tick={{ fill: "#A7ADB5", fontSize: 11 }} allowDecimals={false} />
              <Tooltip
                contentStyle={{
                  background: "#14171D",
                  border: "1px solid rgba(255,255,255,0.1)",
                  borderRadius: 8,
                }}
              />
              <Bar dataKey="count" fill="#E09B6A" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
