"use client";

import { useEffect, useState } from "react";
import { format, parseISO } from "date-fns";
import { fr } from "date-fns/locale";
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
import { Loader2 } from "lucide-react";
import { fetchAffiliateTimeline } from "@/lib/partnerships-api";

interface AffiliateChartProps {
  linkId: string;
}

export function AffiliateChart({ linkId }: AffiliateChartProps) {
  const [data, setData] = useState<
    { label: string; clicks: number; conversions: number }[]
  >([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetchAffiliateTimeline(linkId, 30)
      .then((points) =>
        setData(
          points.map((p) => ({
            label: format(parseISO(p.date), "d MMM", { locale: fr }),
            clicks: p.clicks,
            conversions: p.conversions,
          }))
        )
      )
      .catch(() => setData([]))
      .finally(() => setLoading(false));
  }, [linkId]);

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <Loader2 className="h-5 w-5 animate-spin text-titanium" />
      </div>
    );
  }

  if (!data.length) {
    return (
      <p className="py-8 text-center text-sm text-titanium">
        Pas encore de données sur 30 jours.
      </p>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
        <XAxis
          dataKey="label"
          tick={{ fill: "#a7adb5", fontSize: 10 }}
          interval="preserveStartEnd"
        />
        <YAxis tick={{ fill: "#a7adb5", fontSize: 10 }} allowDecimals={false} />
        <Tooltip
          contentStyle={{
            background: "#14171d",
            border: "1px solid rgba(255,255,255,0.1)",
            borderRadius: 8,
          }}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="clicks"
          name="Clics"
          stroke="#C08A72"
          strokeWidth={2}
          dot={false}
        />
        <Line
          type="monotone"
          dataKey="conversions"
          name="Conversions"
          stroke="#22c55e"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
