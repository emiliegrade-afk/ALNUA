"use client";

import { useCallback, useEffect, useState } from "react";
import { CheckCircle2, Loader2, RefreshCw, ShieldAlert } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  approveWorkflowStep,
  fetchWorkflowRunsWaiting,
  type WorkflowRunSummary,
} from "@/lib/workflow-api";
import { cn } from "@/lib/utils";

type WaitingRun = WorkflowRunSummary & {
  steps_a_verifier?: { step_id: string; label: string; detail: string }[];
};

export function CeoWorkflowsPendingCard() {
  const [runs, setRuns] = useState<WaitingRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchWorkflowRunsWaiting(15);
      setRuns(data.runs as WaitingRun[]);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Workflows indisponibles");
      setRuns([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleApprove(runId: string, stepId: string) {
    const key = `${runId}:${stepId}`;
    setBusy(key);
    try {
      await approveWorkflowStep(runId, stepId);
      toast.success(`Étape ${stepId} approuvée`);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Approbation échouée");
    } finally {
      setBusy(null);
    }
  }

  const pendingCount = runs.reduce(
    (n, r) => n + (r.steps_a_verifier?.length ?? 0),
    0,
  );

  return (
    <Card className="mb-8 border-amber-500/25 bg-transparent">
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div>
          <CardTitle className="flex items-center gap-2 font-title text-lg text-ivory">
            <ShieldAlert className="h-5 w-5 text-amber-400" />
            Workflows en attente
          </CardTitle>
          <p className="mt-1 text-xs text-titanium/65">
            Steps A_VERIFIER — validation CEO (DEC-011 / Phase 30)
          </p>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => void load()}
          disabled={loading || busy != null}
          className="text-titanium/60"
        >
          <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin")} />
        </Button>
      </CardHeader>
      <CardContent className="space-y-3">
        {loading && runs.length === 0 ? (
          <p className="text-sm text-titanium/50">Chargement…</p>
        ) : runs.length === 0 ? (
          <p className="text-xs text-titanium/45">Aucun workflow en attente de validation.</p>
        ) : (
          <>
            <p className="text-xs text-titanium/60">
              {runs.length} run(s) · {pendingCount} step(s) à vérifier
            </p>
            <ul className="space-y-2">
              {runs.map((run) =>
                (run.steps_a_verifier ?? []).map((step) => (
                  <li
                    key={`${run.run_id}-${step.step_id}`}
                    className="rounded-lg border border-amber-500/20 bg-obsidian-deep/40 px-3 py-2"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <div>
                        <p className="text-sm text-ivory/90">{step.label}</p>
                        <p className="text-[10px] text-titanium/50">
                          {run.recipe_id} · {run.run_id.slice(0, 14)}
                        </p>
                      </div>
                      <Button
                        size="sm"
                        variant="outline"
                        className="border-emerald-500/30 text-emerald-300"
                        disabled={busy != null}
                        onClick={() => void handleApprove(run.run_id, step.step_id)}
                      >
                        {busy === `${run.run_id}:${step.step_id}` ? (
                          <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                        ) : (
                          <CheckCircle2 className="mr-1 h-3 w-3" />
                        )}
                        Approuver
                      </Button>
                    </div>
                    {step.detail ? (
                      <p className="mt-1 truncate text-[10px] text-titanium/45">{step.detail}</p>
                    ) : null}
                  </li>
                )),
              )}
            </ul>
          </>
        )}
      </CardContent>
    </Card>
  );
}
