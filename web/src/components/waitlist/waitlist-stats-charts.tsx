"use client";

import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { format, parseISO } from "date-fns";
import { fr } from "date-fns/locale";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { WaitlistStats } from "@/lib/waitlist-api";
import { WaitlistSourceDonut } from "@/components/waitlist/waitlist-source-donut";

interface WaitlistStatsChartsProps {
  stats: WaitlistStats;
}

export function WaitlistStatsCharts({ stats }: WaitlistStatsChartsProps) {
  const timelineData = stats.timeline_7d.map((d) => ({
    ...d,
    label: format(parseISO(d.date), "EEE d", { locale: fr }),
  }));

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card className="border-copper/15 bg-surface/80">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-ivory">
            Inscriptions — 7 derniers jours
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={240}>
            <LineChart data={timelineData}>
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
              <Line
                type="monotone"
                dataKey="count"
                stroke="#C08A72"
                strokeWidth={2}
                dot={{ fill: "#C08A72", r: 4 }}
                activeDot={{ r: 6 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <WaitlistSourceDonut bySource={stats.by_source} />
    </div>
  );
}
