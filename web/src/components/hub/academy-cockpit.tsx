"use client";

import { useCallback, useEffect, useState } from "react";
import { GraduationCap, Loader2, Play, RefreshCw, Sprout } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  fetchAcademyStatus,
  runAcademySprint,
  seedAcademyLevel,
  type AcademyStatus,
} from "@/lib/academy-api";

function GateRow({ label, ok }: { label: string; ok: boolean }) {
  return (
    <div className="flex items-center justify-between text-xs">
      <span className="text-titanium/70">{label}</span>
      <span className={ok ? "text-emerald-400" : "text-titanium/40"}>
        {ok ? "OK" : "—"}
      </span>
    </div>
  );
}

export function AcademyCockpit() {
  const [data, setData] = useState<AcademyStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const status = await fetchAcademyStatus();
      setData(status);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur académie");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleSeed(level: number) {
    setBusy(`seed-${level}`);
    try {
      const res = await seedAcademyLevel(level, { markFirstReady: true });
      toast.success(
        `N${level}: ${res.created_count} créées, ${res.skipped_count} existantes`
      );
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Seed échoué");
    } finally {
      setBusy(null);
    }
  }

  async function handleSprint() {
    const level = data?.progress.current_level ?? 1;
    setBusy("sprint");
    try {
      const res = await runAcademySprint(level);
      const marked =
        (res.agent_ready as { marked_count?: number } | undefined)?.marked_count ?? 0;
      toast.success(`Sprint N${level} — ${marked} issue(s) agent-ready`);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Sprint échoué");
    } finally {
      setBusy(null);
    }
  }

  const progress = data?.progress;
  const currentLevel = progress?.current_level ?? 1;
  const levelKey = String(currentLevel);
  const lv = progress?.levels[levelKey];

  return (
    <Card className="mb-6 border-copper/20 bg-obsidian-2/90">
      <CardHeader className="flex flex-row items-center justify-between gap-4 space-y-0">
        <div>
          <CardTitle className="flex items-center gap-2 font-title text-base text-ivory">
            <GraduationCap className="h-4 w-4 text-copper" />
            Académie ALNUA
          </CardTitle>
          <p className="label-caps mt-1">Entraînement dev_app avant NUAWAY</p>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={() => void load()}
          disabled={loading}
          className="text-titanium/60"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </CardHeader>
      <CardContent className="space-y-4">
        {!data?.repo_configured ? (
          <p className="text-sm text-amber-400/90">
            Configure <code className="text-xs">GITHUB_REPO_ACADEMY</code> et clone le repo
            (ex. <code className="text-xs">C:\Dev\alnua-academy</code>).
          </p>
        ) : null}

        {loading && !data ? (
          <p className="text-sm text-titanium/50">Chargement…</p>
        ) : progress ? (
          <>
            <div className="grid gap-3 sm:grid-cols-3">
              <div className="rounded-lg border border-copper/10 px-3 py-2">
                <p className="text-[10px] uppercase tracking-wider text-titanium/50">
                  Niveau
                </p>
                <p className="font-title text-xl text-ivory">N{currentLevel}</p>
                <p className="text-xs text-titanium/60">{lv?.name}</p>
              </div>
              <div className="rounded-lg border border-copper/10 px-3 py-2">
                <p className="text-[10px] uppercase tracking-wider text-titanium/50">
                  Progression
                </p>
                <p className="font-title text-xl text-ivory">
                  {progress.completed_exercises}/{progress.total_exercises}
                </p>
                <p className="text-xs text-titanium/60">
                  {progress.success_rate_pct}% succès
                </p>
              </div>
              <div className="rounded-lg border border-copper/10 px-3 py-2">
                <p className="text-[10px] uppercase tracking-wider text-titanium/50">
                  N{currentLevel} détail
                </p>
                <p className="font-title text-xl text-ivory">
                  {lv?.done ?? 0}/{lv?.total ?? 0}
                </p>
                <p className="text-xs text-titanium/60">
                  {lv?.failed ?? 0} échec · {lv?.in_progress ?? 0} en cours
                </p>
              </div>
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <p className="text-xs font-medium text-titanium/50">Gate Produit (Lounge)</p>
                {progress.gate_nuaway.gate_open ? (
                  <span className="rounded bg-emerald-500/15 px-2 py-0.5 text-[10px] font-medium text-emerald-400">
                    OPEN
                  </span>
                ) : null}
              </div>
              <div className="space-y-1 rounded-lg border border-copper/10 p-3">
                <GateRow
                  label="Taux succès ≥ 65%"
                  ok={progress.gate_nuaway.success_rate_65}
                />
                <GateRow
                  label="N4 stable"
                  ok={progress.gate_nuaway.academy_n4_stable}
                />
                <GateRow
                  label="Mem0 enrichi"
                  ok={progress.gate_nuaway.mem0_lessons_35}
                />
                <GateRow
                  label="≥ 5 erreurs résolues"
                  ok={Boolean(progress.gate_nuaway.error_journal_top5)}
                />
                <GateRow
                  label="Pipeline Academy actif"
                  ok={Boolean(progress.gate_nuaway.github_pipeline)}
                />
              </div>
            </div>

            {data.mem0_snippet ? (
              <div>
                <p className="mb-1 text-xs text-titanium/50">Dernières leçons Mem0</p>
                <p className="max-h-20 overflow-y-auto rounded bg-black/30 p-2 font-mono text-[10px] text-titanium/70">
                  {data.mem0_snippet.slice(0, 400)}
                </p>
              </div>
            ) : null}

            <div className="flex flex-wrap gap-2">
              {[1, 2, 3, 4].map((n) => (
                <Button
                  key={n}
                  size="sm"
                  variant="outline"
                  disabled={busy !== null}
                  onClick={() => void handleSeed(n)}
                  className="border-copper/20 text-xs"
                >
                  {busy === `seed-${n}` ? (
                    <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                  ) : (
                    <Sprout className="mr-1 h-3 w-3" />
                  )}
                  Seed N{n}
                </Button>
              ))}
              <Button
                size="sm"
                disabled={busy !== null || !data.repo_configured}
                onClick={() => void handleSprint()}
                className="bg-copper/90 text-obsidian hover:bg-copper"
              >
                {busy === "sprint" ? (
                  <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                ) : (
                  <Play className="mr-1 h-3 w-3" />
                )}
                Sprint N{currentLevel}
              </Button>
            </div>
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}
