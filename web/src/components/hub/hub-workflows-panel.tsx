"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Loader2, Play, RefreshCw } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  fetchWorkflowRecipes,
  fetchWorkflowRuns,
  runOpsNow,
  runSemaineNow,
  shipGameRelease,
  shipRoboRelease,
  type WorkflowRecipe,
  type WorkflowRunSummary,
} from "@/lib/workflow-api";
import { cn } from "@/lib/utils";

const P0_RECIPES = new Set(["run_ops", "semaine", "ship_hub", "dossier_ceo"]);
const P2_RECIPES = new Set(["ship_game", "ship_robo"]);

function statusIcon(status: string) {
  if (status === "blocked") return <AlertTriangle className="h-3.5 w-3.5 text-red-400" />;
  if (status === "completed") return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />;
  return null;
}

export function HubWorkflowsPanel() {
  const [recipes, setRecipes] = useState<WorkflowRecipe[]>([]);
  const [runs, setRuns] = useState<WorkflowRunSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState<string | null>(null);
  const [shipSlug, setShipSlug] = useState("wyrdheim");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [r, h] = await Promise.all([
        fetchWorkflowRecipes(),
        fetchWorkflowRuns(15),
      ]);
      setRecipes(r);
      setRuns(h.runs);
    } catch {
      setRecipes([]);
      setRuns([]);
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

  return (
    <Card className="mb-8 border-copper/20 bg-obsidian-2/90">
      <CardHeader className="flex flex-row items-center justify-between gap-4">
        <div>
          <CardTitle className="font-title text-base text-ivory">
            Company OS — ops autonomes
          </CardTitle>
          <p className="mt-1 font-body text-xs text-titanium/60">
            Exécution auto lun–ven 8h15 (ops) · ven 17h (semaine). Toi : choix produit,
            validation CEO, brainstorming.
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
            Releases P2 — gaming & robotique
          </p>
          <div className="mb-2 flex flex-wrap items-center gap-2">
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
          <p className="text-[10px] text-titanium/45">
            Slug dans le registry · branche gaming ou robotics · GDD ou BOM requis
          </p>
        </div>

        {!loading && recipes.length > 0 && (
          <div className="grid gap-2 sm:grid-cols-2">
            {recipes
              .filter((r) => P0_RECIPES.has(r.id) || P2_RECIPES.has(r.id))
              .map((r) => (
              <div
                key={r.id}
                className="rounded-lg border border-copper/10 bg-obsidian-deep/40 px-3 py-2"
              >
                <p className="text-xs font-medium text-ivory/90">{r.name}</p>
                <p className="text-[10px] text-titanium/50">
                  {r.id}
                  {P2_RECIPES.has(r.id) ? " · P2" : ""}
                </p>
              </div>
            ))}
          </div>
        )}

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
              {runs.slice(0, 8).map((run) => (
                <li
                  key={run.run_id}
                  className="flex items-start gap-2 rounded-md border border-copper/10 px-2 py-1.5 text-xs"
                >
                  {statusIcon(run.status)}
                  <div className="min-w-0 flex-1">
                    <span className="text-copper/90">{run.recipe_id}</span>
                    <span
                      className={cn(
                        "ml-2",
                        run.status === "blocked" ? "text-red-400" : "text-titanium/60"
                      )}
                    >
                      {run.status}
                    </span>
                    <p className="truncate text-titanium/50">{run.summary}</p>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
