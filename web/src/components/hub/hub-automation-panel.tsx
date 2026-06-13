"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Play, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  fetchOrchestrationWorkflows,
  runMorningOrchestration,
  type OrchestrationWorkflow,
} from "@/lib/pole-api";

export function HubAutomationPanel() {
  const [workflows, setWorkflows] = useState<OrchestrationWorkflow[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [lastResult, setLastResult] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchOrchestrationWorkflows();
      setWorkflows(data);
    } catch {
      setWorkflows([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleMorning(weekly: boolean) {
    setRunning(true);
    setLastResult(null);
    try {
      const res = await runMorningOrchestration(weekly);
      const plan = typeof res.coo_plan === "string" ? res.coo_plan : JSON.stringify(res, null, 2);
      setLastResult(plan);
      toast.success(weekly ? "Plan de la semaine envoyé" : "Briefing matinal envoyé");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setRunning(false);
    }
  }

  return (
    <Card className="mb-8 border-copper/20 bg-obsidian-2/90">
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <div>
          <CardTitle className="font-title text-base text-ivory">
            Pilotage automatique
          </CardTitle>
          <p className="mt-1 font-body text-xs text-titanium/60">
            Workflows n8n + planificateur Hub — Telegram & Discord si configurés
          </p>
        </div>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="border-copper/30"
          onClick={() => void load()}
          disabled={loading}
        >
          <RefreshCw className={`mr-1 h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          Actualiser
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="border-copper/30 bg-copper/10"
            disabled={running}
            onClick={() => void handleMorning(false)}
          >
            {running ? (
              <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
            ) : (
              <Play className="mr-1 h-3.5 w-3.5" />
            )}
            Briefing du jour
          </Button>
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="border-copper/30"
            disabled={running}
            onClick={() => void handleMorning(true)}
          >
            Plan de la semaine
          </Button>
        </div>

        {loading ? (
          <p className="text-sm text-gray-500">Chargement des workflows…</p>
        ) : workflows.length > 0 ? (
          <ul className="space-y-2 text-xs text-gray-400">
            {workflows.map((wf) => (
              <li
                key={wf.id}
                className="flex flex-wrap items-baseline justify-between gap-2 rounded-lg border border-copper/10 bg-black/20 px-3 py-2"
              >
                <span className="font-medium text-ivory/90">{wf.name}</span>
                <span className="text-titanium/50">{wf.trigger}</span>
              </li>
            ))}
          </ul>
        ) : null}

        {lastResult ? (
          <pre className="max-h-48 overflow-auto rounded-lg border border-copper/10 bg-black/30 p-3 font-mono text-xs text-ivory/80 whitespace-pre-wrap">
            {lastResult}
          </pre>
        ) : null}
      </CardContent>
    </Card>
  );
}
