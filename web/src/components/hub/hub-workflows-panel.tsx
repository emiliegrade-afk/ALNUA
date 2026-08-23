"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AlertTriangle, CheckCircle2, Loader2, Play, RefreshCw, ShieldAlert } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  fetchWorkflowRecipes,
  fetchWorkflowRuns,
  fetchWorkflowRunsWaiting,
  runOpsNow,
  runSemaineNow,
  shipGameRelease,
  shipRoboRelease,
  type WorkflowRecipe,
  type WorkflowRunSummary,
} from "@/lib/workflow-api";
import { ROUTES } from "@/lib/routes";
import { cn } from "@/lib/utils";

const P0_RECIPES = new Set(["run_ops", "semaine", "ship_hub", "dossier_ceo"]);
const P2_RECIPES = new Set(["ship_game", "ship_robo"]);
const VALIDATION_RECIPES = new Set(["content_validation", "campaign_validation"]);

function statusIcon(status: string) {
  if (status === "blocked") return <AlertTriangle className="h-3.5 w-3.5 text-red-400" />;
  if (status === "completed") return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />;
  if (status === "waiting") return <ShieldAlert className="h-3.5 w-3.5 text-amber-400" />;
  return null;
}

function waitingStepCount(run: WorkflowRunSummary): number {
  return run.steps_a_verifier?.length ?? 0;
}

/** Phase 30 — ops + historique + lien CEO pour A_VERIFIER. */
export function HubWorkflowsPanel() {
  const [recipes, setRecipes] = useState<WorkflowRecipe[]>([]);
  const [runs, setRuns] = useState<WorkflowRunSummary[]>([]);
  const [waitingIds, setWaitingIds] = useState<Set<string>>(() => new Set());
  const [waitingCount, setWaitingCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<string | null>(null);
  const [shipSlug, setShipSlug] = useState("wyrdheim");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [r, h, w] = await Promise.all([
        fetchWorkflowRecipes(),
        fetchWorkflowRuns(15),
        fetchWorkflowRunsWaiting(20).catch(() => ({ runs: [] as WorkflowRunSummary[] })),
      ]);
      setRecipes(r);
      setRuns(h.runs);
      setWaitingIds(new Set(w.runs.map((run) => run.run_id)));
      setWaitingCount(
        w.runs.reduce((n, run) => n + Math.max(1, waitingStepCount(run)), 0),
      );
    } catch {
      setRecipes([]);
      setRuns([]);
      setWaitingIds(new Set());
      setWaitingCount(0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function trigger(label: string, fn: () => Promise<unknown>) {
    setRunning(label);
    try {
      const res = await fn();
      const summary =
        typeof res === "object" && res && "summary" in res
          ? String((res as { summary: string }).summary)
          : "Terminé";
      toast.success(summary.slice(0, 120));
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur workflow");
    } finally {
      setRunning(null);
    }
  }

  const shownRecipes = recipes.filter(
    (r) => P0_RECIPES.has(r.id) || P2_RECIPES.has(r.id) || VALIDATION_RECIPES.has(r.id),
  );

  return (
    <Card className="border-copper/20 bg-obsidian-2/90">
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <div>
          <CardTitle className="font-title text-base text-ivory">
            Company OS — workflows
          </CardTitle>
          <p className="mt-1 font-body text-xs text-titanium/60">
            Ops · validation contenu/campagne · ship. Approbations sur{" "}
            <Link href={ROUTES.ceo} className="text-copper hover:underline">
              /ceo
            </Link>
            .
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
          <RefreshCw className={cn("mr-1 h-3.5 w-3.5", loading && "animate-spin")} />
          Actualiser
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {waitingCount > 0 ? (
          <Link
            href={ROUTES.ceo}
            className="flex items-center gap-2 rounded-lg border border-amber-500/30 bg-amber-500/[0.07] px-3 py-2 text-xs text-amber-100/90 transition hover:bg-amber-500/15"
          >
            <ShieldAlert className="h-3.5 w-3.5 shrink-0" />
            <span>
              {waitingCount} étape{waitingCount > 1 ? "s" : ""} en attente — ouvrir le bureau CEO
            </span>
          </Link>
        ) : (
          <p className="text-[11px] text-titanium/50">Aucune étape A_VERIFIER — file CEO vide.</p>
        )}

        <div className="flex flex-wrap gap-2">
          <Button
            type="button"
            size="sm"
            className="bg-copper/90 hover:bg-copper"
            disabled={!!running}
            onClick={() => void trigger("ops", runOpsNow)}
          >
            {running === "ops" ? (
              <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
            ) : (
              <Play className="mr-1 h-3.5 w-3.5" />
            )}
            RUN ops maintenant
          </Button>
          <Button
            type="button"
            size="sm"
            variant="outline"
            className="border-copper/30"
            disabled={!!running}
            onClick={() => void trigger("semaine", runSemaineNow)}
          >
            {running === "semaine" ? (
              <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
            ) : (
              <Play className="mr-1 h-3.5 w-3.5" />
            )}
            Brief semaine
          </Button>
        </div>

        <div className="rounded-lg border border-copper/10 bg-obsidian-deep/40 p-3">
          <p className="mb-2 text-[10px] font-medium uppercase tracking-wide text-titanium/45">
            Releases — gaming & robotique
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <input
              className="w-40 rounded-md border border-titanium/15 bg-obsidian-3 px-2 py-1 text-xs text-ivory"
              value={shipSlug}
              onChange={(e) => setShipSlug(e.target.value)}
              placeholder="slug registry"
            />
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="border-copper/30 text-xs"
              disabled={!!running || !shipSlug.trim()}
              onClick={() =>
                void trigger("ship_game", () => shipGameRelease(shipSlug.trim(), "beta"))
              }
            >
              {running === "ship_game" ? (
                <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
              ) : (
                <Play className="mr-1 h-3.5 w-3.5" />
              )}
              Ship jeu
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              className="border-copper/30 text-xs"
              disabled={!!running || !shipSlug.trim()}
              onClick={() =>
                void trigger("ship_robo", () => shipRoboRelease(shipSlug.trim(), "beta"))
              }
            >
              {running === "ship_robo" ? (
                <Loader2 className="mr-1 h-3.5 w-3.5 animate-spin" />
              ) : (
                <Play className="mr-1 h-3.5 w-3.5" />
              )}
              Ship robo
            </Button>
          </div>
        </div>

        {!loading && shownRecipes.length > 0 ? (
          <div className="grid gap-2 sm:grid-cols-2">
            {shownRecipes.map((r) => (
              <div
                key={r.id}
                className="rounded-lg border border-copper/10 bg-obsidian-deep/40 px-3 py-2"
              >
                <p className="text-xs font-medium text-ivory/90">{r.name}</p>
                <p className="text-[10px] text-titanium/50">
                  {r.id}
                  {VALIDATION_RECIPES.has(r.id)
                    ? " · validation"
                    : P2_RECIPES.has(r.id)
                      ? " · ship"
                      : " · ops"}
                </p>
              </div>
            ))}
          </div>
        ) : null}

        <div>
          <p className="mb-2 text-[10px] font-medium uppercase tracking-wide text-titanium/45">
            Dernières exécutions
          </p>
          {loading ? (
            <p className="text-sm text-titanium/50">Chargement…</p>
          ) : runs.length === 0 ? (
            <p className="text-sm text-titanium/50">Aucun run enregistré.</p>
          ) : (
            <ul className="space-y-1.5">
              {runs.slice(0, 8).map((run) => {
                const waiting = waitingIds.has(run.run_id);
                return (
                  <li
                    key={run.run_id}
                    className="flex items-start gap-2 rounded-md border border-copper/10 px-2 py-1.5 text-xs"
                  >
                    {statusIcon(waiting ? "waiting" : run.status)}
                    <div className="min-w-0 flex-1">
                      <span className="text-copper/90">{run.recipe_id}</span>
                      <span
                        className={cn(
                          "ml-2",
                          waiting
                            ? "text-amber-400"
                            : run.status === "blocked"
                              ? "text-red-400"
                              : "text-titanium/60",
                        )}
                      >
                        {waiting ? "A_VERIFIER" : run.status}
                      </span>
                      <p className="truncate text-titanium/50">{run.summary}</p>
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
