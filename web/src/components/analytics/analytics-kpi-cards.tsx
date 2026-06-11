"use client";

import {
  Download,
  Users,
  Euro,
  TrendingDown,
  Globe,
  Wallet,
} from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import {
  formatChangePct,
  formatKpiValue,
  type AnalyticsSummary,
} from "@/lib/analytics";
import { cn } from "@/lib/utils";

interface AnalyticsKpiCardsProps {
  summary: AnalyticsSummary | null;
  loading?: boolean;
}

const KPI_CONFIG = [
  {
    key: "downloads" as const,
    label: "Total téléchargements",
    icon: Download,
    suffix: undefined as string | undefined,
    isCurrency: false,
    isPercent: false,
  },
  {
    key: "subscriptions" as const,
    label: "Abonnements actifs",
    icon: Users,
    suffix: undefined,
    isCurrency: false,
    isPercent: false,
  },
  {
    key: "mrr" as const,
    label: "MRR",
    icon: Wallet,
    suffix: undefined,
    isCurrency: true,
    isPercent: false,
  },
  {
    key: "churn" as const,
    label: "Churn ce mois",
    icon: TrendingDown,
    suffix: "%",
    isCurrency: false,
    isPercent: true,
  },
  {
    key: "web_visitors" as const,
    label: "Visiteurs web ce mois",
    icon: Globe,
    suffix: undefined,
    isCurrency: false,
    isPercent: false,
  },
  {
    key: "revenue_month" as const,
    label: "Revenus ce mois",
    icon: Euro,
    suffix: undefined,
    isCurrency: true,
    isPercent: false,
  },
];

function KpiSkeleton() {
  return (
    <Card className="border-white/[0.06] bg-surface/80">
      <CardContent className="p-4">
        <div className="h-4 w-24 animate-pulse rounded bg-white/10" />
        <div className="mt-3 h-8 w-20 animate-pulse rounded bg-white/10" />
        <div className="mt-2 h-3 w-16 animate-pulse rounded bg-white/5" />
      </CardContent>
    </Card>
  );
}

export function AnalyticsKpiCards({ summary, loading }: AnalyticsKpiCardsProps) {
  if (loading) {
    return (
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
        {KPI_CONFIG.map((k) => (
          <KpiSkeleton key={k.key} />
        ))}
      </div>
    );
  }

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
      {KPI_CONFIG.map(({ key, label, icon: Icon, suffix, isCurrency, isPercent }) => {
        const kpi = summary?.[key];
        const value = kpi?.value;
        const change = formatChangePct(kpi?.change_pct);

        const displayValue =
          value === null || value === undefined
            ? "–"
            : isPercent
              ? `${formatKpiValue(value)}%`
              : formatKpiValue(value, { suffix, isCurrency });

        return (
          <Card
            key={key}
            className="border-white/[0.06] bg-surface/80 transition hover:border-copper/20"
          >
            <CardContent className="p-4">
              <div className="flex items-center gap-2 text-titanium">
                <Icon className="h-3.5 w-3.5 shrink-0 text-copper/70" />
                <span className="text-[11px] leading-tight">{label}</span>
              </div>
              <p className="mt-2 text-2xl font-semibold tabular-nums text-ivory">
                {displayValue}
              </p>
              {change.text ? (
                <p
                  className={cn(
                    "mt-1 text-[11px] tabular-nums",
                    change.positive === true && "text-emerald-400",
                    change.positive === false && "text-red-400",
                    change.positive === null && "text-titanium/60"
                  )}
                >
                  {change.text} vs mois préc.
                </p>
              ) : (
                <p className="mt-1 text-[11px] text-titanium/40">—</p>
              )}
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
