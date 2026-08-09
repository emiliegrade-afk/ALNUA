"use client";

import { useCallback, useEffect, useState } from "react";
import {
  CheckCircle2,
  Circle,
  Loader2,
  Lock,
  MinusCircle,
  Route,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  fetchDossierPipeline,
  type RndPipelineResponse,
  type RndPipelineStage,
} from "@/lib/rnd-dossier";
import { cn } from "@/lib/utils";

const STATUS_ICON: Record<string, React.ReactNode> = {
  done: <CheckCircle2 className="h-4 w-4 text-emerald-400" />,
  in_progress: <Circle className="h-4 w-4 animate-pulse text-copper" />,
  pending: <Circle className="h-4 w-4 text-titanium/40" />,
  locked: <Lock className="h-4 w-4 text-amber-400/80" />,
  skipped: <MinusCircle className="h-4 w-4 text-titanium/50" />,
};

export interface RndPipelinePanelProps {
  dossierId: string;
  onNavigateTab?: (tab: string) => void;
}

export function RndPipelinePanel({
  dossierId,
  onNavigateTab,
}: RndPipelinePanelProps) {
  const [data, setData] = useState<RndPipelineResponse | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await fetchDossierPipeline(dossierId));
    } catch {
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [dossierId]);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <div className="flex h-48 items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-copper/50" />
      </div>
    );
  }

  if (!data) {
    return (
      <p className="text-center text-sm text-titanium/60">
        Impossible de charger le pipeline.
      </p>
    );
  }

  return (
    <div className="mx-auto flex w-full max-w-2xl flex-col gap-6">
      <div>
        <div className="mb-2 flex items-center gap-2">
          <Route className="h-5 w-5 text-copper" />
          <h2 className="font-title text-xl text-ivory">Pipeline R&D</h2>
        </div>
        <p className="text-sm text-titanium/70">
          Idée → dossier → comité → visuels → social → CEO → fiche produit
        </p>
      </div>

      <div className="rounded-xl border border-copper/15 bg-obsidian-deep/40 p-5">
        <div className="mb-3 flex items-center justify-between gap-3">
          <span className="text-sm text-ivory/90">
            {data.stages_done}/{data.stages_total} étapes
          </span>
          <span className="font-title text-lg text-copper">{data.progress_pct}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-full bg-obsidian/60">
          <div
            className="h-full rounded-full bg-copper transition-all"
            style={{ width: `${data.progress_pct}%` }}
          />
        </div>
        {data.next_action ? (
          <p className="mt-3 text-xs leading-relaxed text-titanium/65">
            {data.next_action}
          </p>
        ) : null}
        {data.pipeline_complete ? (
          <p className="mt-2 text-xs font-medium text-emerald-400">
            Pipeline complet — dossier publié.
          </p>
        ) : null}
      </div>

      <ol className="space-y-2">
        {data.stages.map((stage) => (
          <StageRow
            key={stage.id}
            stage={stage}
            onOpen={
              onNavigateTab && stage.tab && stage.status !== "locked"
                ? () => onNavigateTab(stage.tab!)
                : undefined
            }
          />
        ))}
      </ol>
    </div>
  );
}

function StageRow({
  stage,
  onOpen,
}: {
  stage: RndPipelineStage;
  onOpen?: () => void;
}) {
  const icon = STATUS_ICON[stage.status] ?? STATUS_ICON.pending;
  return (
    <li
      className={cn(
        "flex items-start gap-3 rounded-xl border px-4 py-3",
        stage.status === "done"
          ? "border-emerald-500/20 bg-emerald-500/5"
          : stage.status === "in_progress"
            ? "border-copper/25 bg-copper/5"
            : stage.status === "locked"
              ? "border-amber-500/15 bg-amber-500/5"
              : "border-copper/15 bg-obsidian-deep/40"
      )}
    >
      <div className="mt-0.5 shrink-0">{icon}</div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <span className="text-[10px] font-medium uppercase tracking-wider text-titanium/45">
            Phase {stage.phase}
          </span>
          <span className="text-sm font-medium text-ivory/90">{stage.label}</span>
        </div>
        {stage.detail ? (
          <p className="mt-1 text-xs text-titanium/60">{stage.detail}</p>
        ) : null}
        {stage.public_url ? (
          <p className="mt-1 text-xs text-copper">{stage.public_url}</p>
        ) : null}
      </div>
      {onOpen ? (
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="shrink-0 text-xs text-copper hover:bg-copper/10"
          onClick={onOpen}
        >
          Ouvrir
        </Button>
      ) : null}
    </li>
  );
}
