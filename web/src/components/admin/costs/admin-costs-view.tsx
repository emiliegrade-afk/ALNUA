"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useState } from "react";
import { Loader2, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  fetchCostAlert,
  fetchCostMonthly,
  fetchCostReport,
  fetchTopCosts,
  type CostAlert,
  type CostReport,
  type TopCostCall,
} from "@/lib/admin-costs-api";
import {
  fetchAdminFlags,
  type AdminFlags,
} from "@/lib/admin-flags-api";
import { cn } from "@/lib/utils";

function ChartLoader() {
  return (
    <div className="flex min-h-[220px] items-center justify-center">
      <Loader2 className="h-6 w-6 animate-spin text-copper/50" />
    </div>
  );
}

const CostsByAgentChart = dynamic(
  () =>
    import("@/components/admin/costs/costs-by-agent-chart").then(
      (m) => m.CostsByAgentChart
    ),
  { ssr: false, loading: ChartLoader }
);

function severityClass(severity: CostAlert["severity"]) {
  if (severity === "critical") return "border-red-500/40 bg-red-500/10 text-red-300";
  if (severity === "warning") return "border-amber-500/40 bg-amber-500/10 text-amber-200";
  return "border-emerald-500/30 bg-emerald-500/10 text-emerald-200";
}

export function AdminCostsView() {
  const [days, setDays] = useState(7);
  const [budget, setBudget] = useState(5);
  const [adminFlags, setAdminFlags] = useState<AdminFlags | null>(null);
  const [report, setReport] = useState<CostReport | null>(null);
  const [alert, setAlert] = useState<CostAlert | null>(null);
  const [monthly, setMonthly] = useState<{ total_cost_usd: number; month: string } | null>(
    null
  );
  const [topCalls, setTopCalls] = useState<TopCostCall[]>([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [reportData, alertData, monthlyData, topData] = await Promise.all([
        fetchCostReport(days),
        fetchCostAlert(budget),
        fetchCostMonthly(),
        fetchTopCosts(10, days),
      ]);
      setReport(reportData);
      setAlert(alertData);
      setMonthly({
        total_cost_usd: monthlyData.total_cost_usd,
        month: monthlyData.month,
      });
      setTopCalls(topData);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur chargement coûts");
      setReport(null);
      setAlert(null);
      setMonthly(null);
      setTopCalls([]);
    } finally {
      setLoading(false);
    }
  }, [days, budget]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    fetchAdminFlags()
      .then(setAdminFlags)
      .catch(() => setAdminFlags(null));
  }, []);

  return (
    <div className="space-y-6">
      {adminFlags ? (
        <Card className="border-copper/15 bg-obsidian-2/60">
          <CardContent className="p-4 font-body text-xs text-titanium/80">
            <p className="label-caps mb-2 text-copper/70">Migration coûts (Phase 0)</p>
            <ul className="space-y-1">
              <li>
                <code className="text-copper-light">COSTS_UNIFIED_READ</code>={" "}
                {adminFlags.costs_unified_read ? "activé" : "désactivé"}
              </li>
              <li>
                <code className="text-copper-light">COSTS_SHADOW_COMPARE</code>={" "}
                {adminFlags.costs_shadow_compare ? "activé" : "désactivé"}
              </li>
            </ul>
          </CardContent>
        </Card>
      ) : null}
      <div className="flex flex-wrap items-end gap-4">
        <div>
          <Label htmlFor="costs-days" className="text-titanium/70">
            Période (jours)
          </Label>
          <Input
            id="costs-days"
            type="number"
            min={1}
            max={30}
            value={days}
            onChange={(e) => setDays(Number(e.target.value) || 7)}
            className="mt-1 w-24 border-copper/20 bg-obsidian-2"
          />
        </div>
        <div>
          <Label htmlFor="costs-budget" className="text-titanium/70">
            Budget jour (USD)
          </Label>
          <Input
            id="costs-budget"
            type="number"
            min={0.5}
            step={0.5}
            value={budget}
            onChange={(e) => setBudget(Number(e.target.value) || 5)}
            className="mt-1 w-28 border-copper/20 bg-obsidian-2"
          />
        </div>
        <Button
          type="button"
          variant="outline"
          className="border-copper/30"
          onClick={() => void load()}
          disabled={loading}
        >
          <RefreshCw className={cn("mr-2 h-4 w-4", loading && "animate-spin")} />
          Actualiser
        </Button>
      </div>

      {loading && !report ? (
        <div className="flex justify-center py-16">
          <Loader2 className="h-8 w-8 animate-spin text-copper/60" />
        </div>
      ) : (
        <>
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <Card className="border-copper/20 bg-obsidian-2/80">
              <CardHeader className="pb-2">
                <CardTitle className="font-body text-xs text-titanium/60">
                  Total {days}j
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-title text-2xl text-ivory">
                  ${report?.total_cost_usd?.toFixed(4) ?? "0"}
                </p>
                <p className="text-xs text-titanium/50">
                  {report?.total_calls ?? 0} appels
                </p>
              </CardContent>
            </Card>
            <Card className="border-copper/20 bg-obsidian-2/80">
              <CardHeader className="pb-2">
                <CardTitle className="font-body text-xs text-titanium/60">
                  Mois en cours
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="font-title text-2xl text-ivory">
                  ${monthly?.total_cost_usd?.toFixed(4) ?? "0"}
                </p>
                <p className="text-xs text-titanium/50">{monthly?.month}</p>
              </CardContent>
            </Card>
            {alert && (
              <Card
                className={cn(
                  "border sm:col-span-2 lg:col-span-2",
                  severityClass(alert.severity)
                )}
              >
                <CardHeader className="pb-2">
                  <CardTitle className="font-body text-xs opacity-80">
                    Budget aujourd&apos;hui
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="font-title text-xl">
                    ${alert.spent_usd} / ${alert.daily_budget_usd}
                  </p>
                  <p className="text-sm opacity-80">
                    {alert.pct_used}% · {alert.severity}
                    {alert.alert ? " · alerte active" : ""}
                  </p>
                </CardContent>
              </Card>
            )}
          </div>

          {report && Object.keys(report.by_agent).length > 0 && (
            <Card className="border-copper/20 bg-obsidian-2/80">
              <CardHeader>
                <CardTitle className="font-title text-base text-ivory">
                  Par agent
                </CardTitle>
              </CardHeader>
              <CardContent>
                <CostsByAgentChart byAgent={report.by_agent} />
              </CardContent>
            </Card>
          )}

          <Card className="border-copper/20 bg-obsidian-2/80">
            <CardHeader>
              <CardTitle className="font-title text-base text-ivory">
                Top appels coûteux
              </CardTitle>
            </CardHeader>
            <CardContent>
              {topCalls.length === 0 ? (
                <p className="font-body text-sm text-titanium/60">
                  Aucun appel enregistré sur la période.
                </p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full font-body text-sm">
                    <thead>
                      <tr className="border-b border-copper/10 text-left text-titanium/60">
                        <th className="pb-2 pr-4">Agent</th>
                        <th className="pb-2 pr-4">Modèle</th>
                        <th className="pb-2 pr-4">Méthode</th>
                        <th className="pb-2 pr-4">Date</th>
                        <th className="pb-2 text-right">USD</th>
                      </tr>
                    </thead>
                    <tbody>
                      {topCalls.map((row, i) => (
                        <tr
                          key={`${row.agent_id}-${row.ts}-${i}`}
                          className="border-b border-copper/5 text-titanium"
                        >
                          <td className="py-2 pr-4">{row.agent_id}</td>
                          <td className="py-2 pr-4 max-w-[140px] truncate">
                            {row.model}
                          </td>
                          <td className="py-2 pr-4">{row.method || "—"}</td>
                          <td className="py-2 pr-4">{row.date}</td>
                          <td className="py-2 text-right text-copper-light">
                            ${row.cost_usd?.toFixed(6)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
