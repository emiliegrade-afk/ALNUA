"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, Loader2, RefreshCw, Zap } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  fetchProductionOpsStatus,
  simulateSentryEvent,
  type ProductionOpsStatus,
} from "@/lib/ops-api";

export function ProductionOpsCockpit() {
  const [data, setData] = useState<ProductionOpsStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const status = await fetchProductionOpsStatus();
      setData(status);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur ops production");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleSimulate() {
    setSimulating(true);
    try {
      const res = await simulateSentryEvent({
        title: "Simulated map crash on HomeScreen",
        projectSlug: "hub",
      });
      const action = String(res.action ?? "done");
      toast.success(`Simulation Sentry : ${action}`);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Simulation échouée");
    } finally {
      setSimulating(false);
    }
  }

  const recent = data?.sentry.recent_ingests ?? [];
  const openCount = data?.error_journal.open_count ?? 0;

  return (
    <Card className="mb-8 border-red-500/20 bg-obsidian-2/90">
      <CardHeader className="flex flex-row items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <AlertTriangle className="h-4 w-4 text-red-400/80" />
          <CardTitle className="font-title text-base text-ivory">
            Ops Production (Phase 4)
          </CardTitle>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="border-white/10"
          onClick={() => void load()}
          disabled={loading}
        >
          {loading ? (
            <Loader2 className="h-3 w-3 animate-spin" />
          ) : (
            <RefreshCw className="h-3 w-3" />
          )}
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-xs leading-relaxed text-titanium/65">
          Sentry → error journal → issue GitHub{" "}
          <code className="text-[10px] text-copper/80">[HOTFIX]</code> → bug_watchdog →
          fix_pipeline.
        </p>

        <div className="grid gap-3 sm:grid-cols-3">
          <div className="rounded-lg border border-white/10 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-titanium/50">
              Fingerprints
            </p>
            <p className="font-title text-lg text-ivory">
              {data?.sentry.tracked_fingerprints ?? "—"}
            </p>
          </div>
          <div className="rounded-lg border border-white/10 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-titanium/50">
              Erreurs ouvertes
            </p>
            <p className="font-title text-lg text-ivory">{openCount}</p>
          </div>
          <div className="rounded-lg border border-white/10 px-3 py-2">
            <p className="text-[10px] uppercase tracking-wide text-titanium/50">
              Auto-issue
            </p>
            <p className="font-title text-lg text-ivory">
              {data?.sentry.auto_issue ? "ON" : "OFF"}
            </p>
          </div>
        </div>

        {recent.length > 0 ? (
          <ul className="space-y-1 text-xs text-titanium/70">
            {recent.slice(0, 5).map((r) => (
              <li key={`${r.fingerprint}-${r.at}`} className="truncate">
                {r.title}
                {r.issue_number ? ` → #${r.issue_number}` : ""}
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs text-titanium/45">Aucun ingest Sentry récent.</p>
        )}

        <div className="flex flex-wrap items-center gap-2">
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="border-red-500/30 text-red-200"
            onClick={() => void handleSimulate()}
            disabled={simulating}
          >
            {simulating ? (
              <Loader2 className="mr-2 h-3 w-3 animate-spin" />
            ) : (
              <Zap className="mr-2 h-3 w-3" />
            )}
            Simuler alerte Sentry
          </Button>
          <code className="text-[10px] text-titanium/45">
            Webhook : POST {data?.webhook_url ?? "/webhook/sentry"}
          </code>
        </div>
      </CardContent>
    </Card>
  );
}
