"use client";

import { useCallback, useEffect, useState } from "react";
import {
  BookCheck,
  Brain,
  CheckCircle2,
  Loader2,
  Radio,
  Send,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  BUREAU_LABELS,
} from "@/components/library/bureau-library-panel";
import {
  cancelLibraryJob,
  distributeAllLibrary,
  fetchLibraryEnrichStatus,
  learnPendingLibrary,
  verifyLibraryMem0,
  type LibraryDistributionStatus,
} from "@/lib/library-api";
import { cn } from "@/lib/utils";

function ProgressBar({
  label,
  pct,
  detail,
  tone = "bronze",
}: {
  label: string;
  pct: number;
  detail: string;
  tone?: "bronze" | "emerald" | "amber";
}) {
  const bar =
    tone === "emerald"
      ? "bg-emerald-500"
      : tone === "amber"
        ? "bg-amber-400"
        : "bg-bronze-bright";

  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-titane/70">{label}</span>
        <span className="font-mono text-ivoire">{pct}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-obsidian-deep">
        <div
          className={cn("h-full rounded-full transition-all duration-500", bar)}
          style={{ width: `${Math.min(100, pct)}%` }}
        />
      </div>
      <p className="mt-1 text-[10px] text-titane/45">{detail}</p>
    </div>
  );
}

export function LibraryDistributionCard() {
  const [status, setStatus] = useState<LibraryDistributionStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const data = await fetchLibraryEnrichStatus();
      setStatus(data);
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Statut distribution indisponible",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
    const interval =
      status?.active_job?.status === "running" ||
      status?.active_job?.status === "queued"
        ? 8000
        : 20000;
    const t = setInterval(() => void load(), interval);
    return () => clearInterval(t);
  }, [load, status?.active_job?.status]);

  async function runAction(
    key: string,
    fn: () => Promise<{ success: boolean; message: string }>,
  ) {
    setBusy(key);
    try {
      const res = await fn();
      if (res.success) {
        toast.success(res.message);
      } else {
        toast.message(res.message);
      }
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Action échouée");
    } finally {
      setBusy(null);
    }
  }

  const job = status?.active_job;
  const jobRunning = job?.status === "running" || job?.status === "queued";

  return (
    <Card className="mb-8 border-bronze-faint bg-obsidian-2/90">
      <CardHeader className="space-y-1">
        <CardTitle className="flex items-center gap-2 font-title text-base text-ivoire">
          <BookCheck className="h-4 w-4 text-bronze-bright" />
          Distribution &amp; apprentissage agents
        </CardTitle>
        <p className="font-body text-xs text-titane/60">
          Chaque fiche est envoyée aux agents du bureau (Mem0). Lance
          l&apos;apprentissage séparément pour ne pas saturer le serveur.
        </p>
      </CardHeader>
      <CardContent className="space-y-5">
        {loading && !status ? (
          <p className="flex items-center gap-2 text-sm text-titane/50">
            <Loader2 className="h-4 w-4 animate-spin" />
            Chargement du statut…
          </p>
        ) : status ? (
          <>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-lg border border-bronze-faint bg-obsidian-deep/50 p-3">
                <p className="text-[10px] uppercase tracking-wider text-titane/45">
                  Fiches
                </p>
                <p className="font-mono text-xl text-ivoire">
                  {status.total_entries.toLocaleString("fr-FR")}
                </p>
                <p className="text-[11px] text-titane/50">
                  {status.entries_fully_distributed.toLocaleString("fr-FR")}{" "}
                  entièrement distribuées
                </p>
              </div>
              <div className="rounded-lg border border-bronze-faint bg-obsidian-deep/50 p-3">
                <p className="text-[10px] uppercase tracking-wider text-titane/45">
                  En attente
                </p>
                <p className="font-mono text-xl text-amber-300">
                  {status.entries_pending_distribution.toLocaleString("fr-FR")}
                </p>
                <p className="text-[11px] text-titane/50">
                  fiches pas encore à tous les agents
                </p>
              </div>
              <div className="rounded-lg border border-bronze-faint bg-obsidian-deep/50 p-3">
                <p className="text-[10px] uppercase tracking-wider text-titane/45">
                  Couverture agents
                </p>
                <p className="font-mono text-xl text-ivoire">
                  {status.total_slots.toLocaleString("fr-FR")}
                </p>
                <p className="text-[11px] text-titane/50">
                  liaisons fiche × agent attendues
                </p>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-3">
              <ProgressBar
                label="Distribué (Mem0)"
                pct={status.distribution_pct}
                detail={`${status.distributed_slots.toLocaleString("fr-FR")} / ${status.total_slots.toLocaleString("fr-FR")}`}
              />
              <ProgressBar
                label="Appris (leçons LLM)"
                pct={status.learned_pct}
                detail={`${status.learned_slots.toLocaleString("fr-FR")} leçons enregistrées`}
                tone="emerald"
              />
              <ProgressBar
                label="Vérifié dans Mem0"
                pct={status.verified_pct}
                detail={`${status.mem0_confirmed_slots.toLocaleString("fr-FR")} confirmé(s)`}
                tone="amber"
              />
            </div>

            {job ? (
              <div
                className={cn(
                  "rounded-lg border px-3 py-2 text-xs",
                  jobRunning
                    ? "border-bronze/40 bg-bronze/10 text-bronze-bright"
                    : "border-bronze-faint bg-obsidian-deep/40 text-titane/70",
                )}
              >
                <p className="flex items-center gap-2 font-medium">
                  {jobRunning ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  ) : (
                    <CheckCircle2 className="h-3.5 w-3.5" />
                  )}
                  Job {job.kind} — {job.status}
                </p>
                <p className="mt-1">{job.message}</p>
                {job.total > 0 ? (
                  <p className="mt-1 font-mono text-[10px]">
                    {job.processed}/{job.total}
                    {job.distributed ? ` · ${job.distributed} diffusions` : ""}
                    {job.learned ? ` · ${job.learned} leçons` : ""}
                  </p>
                ) : null}
              </div>
            ) : null}

            <div className="flex flex-wrap gap-2">
              <Button
                size="sm"
                className="gap-1.5 bg-bronze text-obsidian hover:bg-bronze-bright"
                disabled={!!busy || jobRunning}
                onClick={() =>
                  void runAction("distribute", () =>
                    distributeAllLibrary({
                      skip_distributed: true,
                      run_learning: false,
                    }),
                  )
                }
              >
                {busy === "distribute" ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Send className="h-3.5 w-3.5" />
                )}
                Distribuer tout (1 clic)
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="gap-1.5 border-bronze-faint"
                disabled={!!busy || jobRunning}
                onClick={() =>
                  void runAction("learn", () => learnPendingLibrary())
                }
              >
                {busy === "learn" ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Brain className="h-3.5 w-3.5" />
                )}
                Apprendre (leçons)
              </Button>
              <Button
                size="sm"
                variant="outline"
                className="gap-1.5 border-bronze-faint"
                disabled={!!busy || jobRunning}
                onClick={() =>
                  void runAction("verify", () => verifyLibraryMem0())
                }
              >
                {busy === "verify" ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Radio className="h-3.5 w-3.5" />
                )}
                Vérifier Mem0
              </Button>
              {jobRunning ? (
                <Button
                  size="sm"
                  variant="outline"
                  className="gap-1.5 border-red-500/30 text-xs text-red-300"
                  disabled={!!busy}
                  onClick={() => void runAction("cancel", () => cancelLibraryJob())}
                >
                  Annuler job
                </Button>
              ) : null}
              <Button
                size="sm"
                variant="ghost"
                className="text-xs text-titane/60"
                disabled={loading}
                onClick={() => void load()}
              >
                Rafraîchir
              </Button>
            </div>

            {Object.keys(status.by_bureau).length > 0 ? (
              <details className="rounded-lg border border-bronze-faint bg-obsidian-deep/30 p-3">
                <summary className="cursor-pointer text-xs font-medium text-titane/70">
                  Détail par bureau
                </summary>
                <ul className="mt-3 space-y-2">
                  {Object.entries(status.by_bureau).map(([bureau, row]) => {
                    const pct =
                      row.slots > 0
                        ? Math.round((row.distributed / row.slots) * 100)
                        : 0;
                    return (
                      <li
                        key={bureau}
                        className="flex flex-wrap items-center justify-between gap-2 text-[11px]"
                      >
                        <span className="text-ivoire">
                          {BUREAU_LABELS[bureau] ?? bureau}
                        </span>
                        <span className="font-mono text-titane/55">
                          {row.entries} fiches · {pct}% distribué ·{" "}
                          {row.learned}/{row.slots} appris
                        </span>
                      </li>
                    );
                  })}
                </ul>
              </details>
            ) : null}
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}
