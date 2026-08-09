"use client";

import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  WAITLIST_SOURCE_COLORS,
  WAITLIST_SOURCE_LABELS,
} from "@/components/waitlist/waitlist.constants";

interface WaitlistSourceDonutProps {
  bySource: Record<string, number>;
}

export function WaitlistSourceDonut({ bySource }: WaitlistSourceDonutProps) {
  const data = Object.entries(bySource).map(([source, count]) => ({
    name: WAITLIST_SOURCE_LABELS[source] ?? source,
    value: count,
  }));

  if (data.length === 0) {
    return (
      <Card className="border-copper/15 bg-surface/80">
        <CardHeader>
          <CardTitle className="text-sm font-medium text-ivory">
            Sources d&apos;inscription
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-titanium">Aucune inscription</CardContent>
      </Card>
    );
  }

  return (
    <Card className="border-copper/15 bg-surface/80">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-ivory">
          Sources d&apos;inscription
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={240}>
          <PieChart>
            <Pie
              data={data}
              dataKey="value"
              nameKey="name"
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={80}
              paddingAngle={2}
            >
              {data.map((_, i) => (
                <Cell
                  key={i}
                  fill={WAITLIST_SOURCE_COLORS[i % WAITLIST_SOURCE_COLORS.length]}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                background: "#14171D",
                border: "1px solid rgba(255,255,255,0.1)",
                borderRadius: 8,
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
