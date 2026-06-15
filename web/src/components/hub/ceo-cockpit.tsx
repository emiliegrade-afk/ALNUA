"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Crown, Loader2, RefreshCw, Rocket, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  evaluateNuawayGate,
  fetchCeoCockpit,
  setCeoBetaGo,
  type BetaCriterion,
  type CeoCockpit,
  type GateCriterion,
} from "@/lib/autonomy-api";
import { ceoDossierHref } from "@/lib/rnd-dossier";
import { cn } from "@/lib/utils";

function CriterionRow({ c }: { c: GateCriterion }) {
  return (
    <div className="flex items-center justify-between gap-2 text-xs">
      <span className={cn("text-titanium/70", c.critical && "text-ivory/80")}>
        {c.critical ? "● " : "○ "}
        {c.label}
      </span>
      <span className={c.passed ? "text-emerald-400" : "text-titanium/40"}>
        {c.passed ? "OK" : "—"}
      </span>
    </div>
  );
}

export function CeoCockpitPanel() {
  const [data, setData] = useState<CeoCockpit | null>(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [ceoGoLoading, setCeoGoLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await fetchCeoCockpit());
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur cockpit CEO");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleEvaluate() {
    setEvaluating(true);
    try {
      const r = await evaluateNuawayGate();
      toast.success(r.message ?? "Gate évaluée");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Évaluation échouée");
    } finally {
      setEvaluating(false);
    }
  }

  async function handleCeoGo() {
    setCeoGoLoading(true);
    try {
      const r = await setCeoBetaGo(true, "Go beta NUAWAY — cockpit CEO");
      toast.success(r.message ?? "Go CEO enregistré");
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Go CEO échoué");
    } finally {
      setCeoGoLoading(false);
    }
  }

  const gate = data?.nuaway_gate;
  const beta = data?.beta_readiness;
  const queue = data?.ceo_queue;

  return (
    <Card className="mb-8 border-copper/30 bg-gradient-to-br from-obsidian-2/95 to-copper/[0.06]">
      <CardHeader className="flex flex-row items-start justify-between gap-4 space-y-0">
        <div>
          <CardTitle className="flex items-center gap-2 font-title text-lg text-ivory">
            <Crown className="h-5 w-5 text-copper" />
            Cockpit CEO — Gate NUAWAY
          </CardTitle>
          <p className="mt-1 text-xs leading-relaxed text-titanium/65">
            {data?.headline ?? "Readiness agents avant beta NUAWAY"}
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => void load()}
            disabled={loading}
            className="text-titanium/60"
          >
            <RefreshCw className={cn("h-3.5 w-3.5", loading && "animate-spin")} />
          </Button>
          <Button
            size="sm"
            variant="outline"
            className="border-copper/30 text-copper"
            onClick={() => void handleEvaluate()}
            disabled={evaluating}
          >
            {evaluating ? (
              <Loader2 className="mr-1 h-3 w-3 animate-spin" />
            ) : (
              <ShieldCheck className="mr-1 h-3 w-3" />
            )}
            Évaluer gate
          </Button>
        </div>
      </CardHeader>
      <CardContent className="space-y-5">
        {loading && !data ? (
          <p className="text-sm text-titanium/50">Chargement…</p>
        ) : gate ? (
          <>
            <div className="flex flex-wrap items-center gap-4">
              <div
                className={cn(
                  "flex h-20 w-20 flex-col items-center justify-center rounded-full border-2",
                  gate.gate_open
                    ? "border-emerald-500/50 bg-emerald-500/10 text-emerald-300"
                    : "border-copper/40 bg-copper/5 text-copper"
                )}
              >
                <span className="font-title text-2xl">{gate.readiness_pct}%</span>
                <span className="text-[9px] uppercase tracking-wide opacity-70">
                  {gate.gate_open ? "OPEN" : "LOCK"}
                </span>
              </div>
              <div className="min-w-0 flex-1 space-y-1 text-xs text-titanium/70">
                <p>
                  Critiques : {gate.critical_passed}/{gate.critical_total} · Total{" "}
                  {gate.passed}/{gate.total}
                </p>
                <p>
                  Pipeline : {data?.pipeline.agent_ready_count ?? 0} issues agent-ready
                  {data?.pipeline.nomad_repo ? ` · ${data.pipeline.nomad_repo}` : ""}
                </p>
              </div>
            </div>

            <div className="grid gap-4 lg:grid-cols-2">
              <div className="rounded-lg border border-white/10 p-3">
                <p className="mb-2 text-xs font-medium text-titanium/50">
                  Critères gate agents
                </p>
                <div className="space-y-1">
                  {(gate.criteria ?? []).map((c) => (
                    <CriterionRow key={c.id} c={c} />
                  ))}
                </div>
              </div>

              <div className="rounded-lg border border-white/10 p-3">
                <div className="mb-2 flex items-center justify-between">
                  <p className="text-xs font-medium text-titanium/50">
                    Checklist beta (Phase 6)
                  </p>
                  {beta?.beta_ready ? (
                    <span className="rounded bg-emerald-500/15 px-2 py-0.5 text-[10px] text-emerald-400">
                      BETA READY
                    </span>
                  ) : null}
                </div>
                <div className="space-y-1">
                  {(beta?.criteria ?? []).map((c: BetaCriterion) => (
                    <CriterionRow key={`beta-${c.id}`} c={c} />
                  ))}
                </div>
                <Button
                  size="sm"
                  className="mt-3 w-full bg-copper/90 text-obsidian hover:bg-copper"
                  onClick={() => void handleCeoGo()}
                  disabled={ceoGoLoading || beta?.ceo_beta?.approved}
                >
                  {ceoGoLoading ? (
                    <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                  ) : (
                    <Rocket className="mr-1 h-3 w-3" />
                  )}
                  {beta?.ceo_beta?.approved ? "Go CEO enregistré" : "Go beta CEO"}
                </Button>
              </div>
            </div>

            <div className="rounded-lg border border-white/10 p-3">
              <p className="mb-2 text-xs font-medium text-titanium/50">File CEO R&D</p>
                {(queue?.to_validate?.length ?? 0) === 0 &&
                (queue?.to_prepare?.length ?? 0) === 0 ? (
                  <p className="text-xs text-titanium/45">Aucun dossier en attente.</p>
                ) : (
                  <ul className="space-y-2 text-xs">
                    {queue?.to_validate?.slice(0, 4).map((d) => (
                      <li key={d.id}>
                        <Link
                          href={ceoDossierHref(d, "ceo")}
                          className="text-copper hover:underline"
                        >
                          {d.title}
                        </Link>
                        {d.recommendation ? (
                          <span className="ml-1 text-titanium/50">({d.recommendation})</span>
                        ) : null}
                      </li>
                    ))}
                    {queue?.to_prepare?.slice(0, 2).map((d) => (
                      <li key={`prep-${d.id}`} className="text-titanium/55">
                        À préparer : {d.title}
                      </li>
                    ))}
                  </ul>
                )}
            </div>
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}
