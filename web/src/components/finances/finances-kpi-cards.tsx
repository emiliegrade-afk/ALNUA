"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { formatCurrency } from "@/lib/finances-api";
import type { MonthTotals } from "@/lib/finances-api";
import { cn } from "@/lib/utils";

interface FinancesKpiCardsProps {
  totals: MonthTotals;
  recurringCount: number;
  ytdBalance: number;
}

export function FinancesKpiCards({
  totals,
  recurringCount,
  ytdBalance,
}: FinancesKpiCardsProps) {
  const balancePositive = totals.balance >= 0;

  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <Card className="border-emerald-500/20 bg-surface/80">
        <CardContent className="p-4">
          <p className="text-sm text-titanium">💚 Revenus du mois</p>
          <p className="mt-2 text-2xl font-semibold tabular-nums text-emerald-400">
            {formatCurrency(totals.total_income)}
          </p>
        </CardContent>
      </Card>

      <Card className="border-red-500/20 bg-surface/80">
        <CardContent className="p-4">
          <p className="text-sm text-titanium">🔴 Dépenses du mois</p>
          <p className="mt-2 text-2xl font-semibold tabular-nums text-red-400">
            {formatCurrency(totals.total_expenses)}
          </p>
        </CardContent>
      </Card>

      <Card
        className={cn(
          "bg-surface/80",
          balancePositive ? "border-emerald-500/20" : "border-red-500/20"
        )}
      >
        <CardContent className="p-4">
          <p className="text-sm text-titanium">⚖️ Balance</p>
          <p
            className={cn(
              "mt-2 text-2xl font-semibold tabular-nums",
              balancePositive ? "text-emerald-400" : "text-red-400"
            )}
          >
            {formatCurrency(totals.balance)}
          </p>
          <p className="mt-1 text-xs text-titanium">
            YTD : {formatCurrency(ytdBalance)}
          </p>
        </CardContent>
      </Card>

      <Card className="border-copper/20 bg-surface/80">
        <CardContent className="p-4">
          <p className="text-sm text-titanium">🔄 Dépenses récurrentes</p>
          <div className="mt-2 flex items-center gap-2">
            <p className="text-2xl font-semibold tabular-nums text-copper-glow">
              {recurringCount}
            </p>
            {recurringCount > 0 ? (
              <Badge variant="outline" className="border-copper/30 text-copper-glow">
                {recurringCount} active{recurringCount > 1 ? "s" : ""}
              </Badge>
            ) : null}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
