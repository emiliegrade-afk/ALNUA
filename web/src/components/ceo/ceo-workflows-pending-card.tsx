"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  ExternalLink,
  Loader2,
  RefreshCw,
  ShieldAlert,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CeoSlideCard, CeoSlideRail } from "@/components/ceo/ceo-slide-rail";
import {
  approveWorkflowStep,
  fetchWorkflowRecipes,
  fetchWorkflowRunsWaiting,
  rejectWorkflowStep,
  type WorkflowRecipe,
  type WorkflowRunSubject,
  type WorkflowRunSummary,
} from "@/lib/workflow-api";
import { ROUTES } from "@/lib/routes";
import { cn } from "@/lib/utils";

const WORKFLOW_EXPLAINER =
  "Un workflow = une procédure auto du Hub. Chaque demande ci-dessous est liée à un objet (dossier R&D, app, ticket…) quand le contexte existe. Lis l’objet avant d’approuver ou de rejeter.";

type WaitingRun = WorkflowRunSummary;

type FlatStep = {
  runId: string;
  recipeId: string;
  recipeName: string;
  recipeDesc: string;
  stepId: string;
  label: string;
  detail: string;
  gaps: string[];
  summary: string;
  subject: WorkflowRunSubject;
};

function recipeHelp(recipeId: string, recipes: WorkflowRecipe[]): { name: string; desc: string } {
  const hit = recipes.find((r) => r.id === recipeId);
  if (hit) return { name: hit.name, desc: hit.description };
  return {
    name: recipeId,
    desc: "Procédure Hub en pause — ton OK ou ton rejet décide de la suite.",
  };
}

export function CeoWorkflowsPendingCard() {
  const [runs, setRuns] = useState<WaitingRun[]>([]);
  const [recipes, setRecipes] = useState<WorkflowRecipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [data, recipeList] = await Promise.all([
        fetchWorkflowRunsWaiting(15),
        fetchWorkflowRecipes().catch(() => [] as WorkflowRecipe[]),
      ]);
      setRuns(data.runs);
      setRecipes(recipeList);
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
    const key = `ok:${runId}:${stepId}`;
    setBusy(key);
    try {
      await approveWorkflowStep(runId, stepId);
      toast.success("Étape validée — le workflow continue");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Approbation échouée");
    } finally {
      setBusy(null);
    }
  }

  async function handleReject(runId: string, stepId: string, subjectLabel: string) {
    const key = `no:${runId}:${stepId}`;
    setBusy(key);
    try {
      await rejectWorkflowStep(
        runId,
        stepId,
        `Refus CEO sur « ${subjectLabel} »`,
      );
      toast.success("Étape rejetée — workflow annulé");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Rejet échoué");
    } finally {
      setBusy(null);
    }
  }

  const steps: FlatStep[] = useMemo(
    () =>
      runs.flatMap((run) => {
        const help = recipeHelp(run.recipe_id, recipes);
        const subject: WorkflowRunSubject = run.subject ?? {
          kind: "none",
          label: "Sans objet lié",
          blurb: "Pas de dossier / app dans le contexte de ce run.",
        };
        return (run.steps_a_verifier ?? []).map((step) => ({
          runId: run.run_id,
          recipeId: run.recipe_id,
          recipeName: help.name,
          recipeDesc: help.desc,
          stepId: step.step_id,
          label: step.label,
          detail: step.detail ?? "",
          gaps: step.gaps ?? [],
          summary: run.summary ?? "",
          subject,
        }));
      }),
    [runs, recipes],
  );

  return (
    <Card className="border-amber-500/25 bg-transparent">
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0 pb-2">
        <div className="min-w-0 flex-1">
          <CardTitle className="flex items-center gap-2 font-title text-base text-ivory">
            <ShieldAlert className="h-4 w-4 text-amber-400" />
            Workflows en attente
          </CardTitle>
          <p className="mt-2 rounded-lg border border-amber-500/25 bg-amber-500/[0.06] px-3 py-2 text-[12px] leading-relaxed text-ivory/85">
            {WORKFLOW_EXPLAINER}{" "}
            <Link href={ROUTES.hub} className="text-copper hover:underline">
              Lancer / suivre les runs → Direction
            </Link>
            .
          </p>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => void load()}
          disabled={loading || busy != null}
          className="shrink-0 text-titanium/60"
        >
          <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin")} />
        </Button>
      </CardHeader>
      <CardContent>
        {loading && steps.length === 0 ? (
          <p className="text-sm text-titanium/50">Chargement…</p>
        ) : steps.length === 0 ? (
          <p className="text-xs leading-relaxed text-titanium/55">
            Aucun workflow en attente de ton OK.
          </p>
        ) : (
          <CeoSlideRail ariaLabel="Workflows en attente" maxHeightClass="max-h-[380px]">
            {steps.map((s) => (
              <CeoSlideCard
                key={`${s.runId}-${s.stepId}`}
                className="border-amber-500/20"
                interactive={false}
              >
                <p className="text-[10px] font-semibold uppercase tracking-wide text-amber-200/90">
                  Workflow · {s.recipeName}
                </p>
                <p className="mt-1 text-[11px] leading-relaxed text-titanium/70">{s.recipeDesc}</p>

                <div className="mt-3 rounded-lg border border-copper/25 bg-copper/[0.07] px-3 py-2">
                  <p className="text-[10px] uppercase tracking-wider text-copper/80">
                    Objet concerné
                  </p>
                  <p className="mt-0.5 text-sm font-medium text-ivory">{s.subject.label}</p>
                  {s.subject.blurb ? (
                    <p className="mt-1 text-[11px] leading-relaxed text-ivory/75">
                      {s.subject.blurb}
                    </p>
                  ) : null}
                  {s.subject.href ? (
                    <Link
                      href={s.subject.href}
                      className="mt-2 inline-flex items-center gap-1 text-[11px] text-copper hover:underline"
                    >
                      <ExternalLink className="h-3 w-3" />
                      Ouvrir l’objet lié
                    </Link>
                  ) : (
                    <p className="mt-2 text-[10px] text-amber-200/80">
                      Pas de lien — lis le détail d’étape ci-dessous avant de décider.
                    </p>
                  )}
                </div>

                <p className="mt-3 text-sm font-medium text-ivory">
                  Étape : {s.label}
                </p>
                <p className="mt-1.5 whitespace-pre-wrap text-[12px] leading-relaxed text-ivory/80">
                  {s.detail.trim() ||
                    "Le Hub demande ton feu vert sur cette étape — aucun détail technique supplémentaire."}
                </p>
                {s.gaps.length > 0 ? (
                  <p className="mt-1 text-[10px] text-titanium/50">
                    Points signalés : {s.gaps.join(" · ")}
                  </p>
                ) : null}
                {s.summary ? (
                  <p className="mt-2 text-[11px] leading-relaxed text-titanium/60">
                    Run : {s.summary}
                  </p>
                ) : null}

                <div className="mt-3 grid grid-cols-2 gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-emerald-500/30 text-emerald-300"
                    disabled={busy != null}
                    onClick={() => void handleApprove(s.runId, s.stepId)}
                  >
                    {busy === `ok:${s.runId}:${s.stepId}` ? (
                      <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                    ) : (
                      <CheckCircle2 className="mr-1 h-3 w-3" />
                    )}
                    Approuver
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="border-danger/40 text-danger"
                    disabled={busy != null}
                    onClick={() => void handleReject(s.runId, s.stepId, s.subject.label)}
                  >
                    {busy === `no:${s.runId}:${s.stepId}` ? (
                      <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                    ) : (
                      <XCircle className="mr-1 h-3 w-3" />
                    )}
                    Rejeter
                  </Button>
                </div>
              </CeoSlideCard>
            ))}
          </CeoSlideRail>
        )}
      </CardContent>
    </Card>
  );
}
