"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  Crown,
  FolderOpen,
  GitBranch,
  Loader2,
  Rocket,
  RotateCcw,
  Send,
  XCircle,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { MarkdownContent } from "@/components/shared/markdown-content";
import {
  decideCeoPackage,
  decomposePrdToIssues,
  dispatchToCoo,
  executeDispatchAgents,
  fetchCeoPackage,
  generateCeoPackage,
  generateEngineeringSpec,
  type CeoPackageResponse,
  type DossierStatus,
} from "@/lib/rnd-dossier";
import { cn } from "@/lib/utils";

export interface RndCeoPanelProps {
  dossierId: string;
  dossierTitle: string;
  dossierStatus: DossierStatus;
  onUpdated?: () => void;
}

const STATUS_LABELS: Record<string, string> = {
  pending: "En attente",
  ready: "Prêt à dispatcher",
  dispatched: "Dispatché au COO",
};

export function RndCeoPanel({
  dossierId,
  dossierTitle,
  dossierStatus,
  onUpdated,
}: RndCeoPanelProps) {
  const [data, setData] = useState<CeoPackageResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [deciding, setDeciding] = useState<string | null>(null);
  const [dispatching, setDispatching] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [generatingSpec, setGeneratingSpec] = useState(false);
  const [decomposing, setDecomposing] = useState(false);
  const [ceoNote, setCeoNote] = useState("");
  const [showNote, setShowNote] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const pkg = await fetchCeoPackage(dossierId);
      setData(pkg);
      setCeoNote(pkg.ceo_note ?? "");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur chargement dossier CEO");
      setData(null);
    } finally {
      setLoading(false);
    }
  }, [dossierId]);

  useEffect(() => {
    void load();
  }, [load]);

  async function handleGenerate(force = false) {
    setGenerating(true);
    try {
      const r = await generateCeoPackage(dossierId, { force });
      toast.success(r.message);
      await load();
      onUpdated?.();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Génération impossible");
    } finally {
      setGenerating(false);
    }
  }

  async function handleDecide(
    status: "approved" | "rejected" | "pivot_requested"
  ) {
    setDeciding(status);
    try {
      const r = await decideCeoPackage(dossierId, {
        ceo_status: status,
        ceo_note: ceoNote.trim() || undefined,
      });
      toast.success(r.message);
      await load();
      onUpdated?.();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Décision impossible");
    } finally {
      setDeciding(null);
      setShowNote(false);
    }
  }

  async function handleDispatch() {
    setDispatching(true);
    try {
      const r = await dispatchToCoo(dossierId);
      toast.success(r.message);
      await load();
      onUpdated?.();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Dispatch impossible");
    } finally {
      setDispatching(false);
    }
  }

  async function handleExecuteAgents() {
    setExecuting(true);
    try {
      const r = await executeDispatchAgents(dossierId);
      toast.success(r.message ?? "Agents lancés");
      await load();
      onUpdated?.();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Exécution impossible");
    } finally {
      setExecuting(false);
    }
  }

  async function handleGenerateSpec(force = false) {
    setGeneratingSpec(true);
    try {
      const r = await generateEngineeringSpec(dossierId, { force });
      toast.success(r.message);
      await load();
      onUpdated?.();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Spec engineering impossible");
    } finally {
      setGeneratingSpec(false);
    }
  }

  async function handleDecomposePrd(dryRun = false) {
    setDecomposing(true);
    try {
      const r = await decomposePrdToIssues(dossierId, { dryRun });
      toast.success(
        dryRun
          ? `Dry-run : ${r.created_count} issues simulées`
          : r.message
      );
      await load();
      onUpdated?.();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Décomposition PRD impossible");
    } finally {
      setDecomposing(false);
    }
  }

  const markdown = data?.markdown ?? "";
  const recommendation = data?.package?.recommendation as string | undefined;
  const matrix = (data?.package?.dispatch_matrix ?? data?.dispatch?.matrix ?? []) as Array<{
    pole: string;
    agent_id: string;
    deliverables: string[];
    priority: string;
  }>;
  const executionStatus = (
    data?.dispatch as { execution_status?: string } | undefined
  )?.execution_status;
  // Item 6 — workspace path (disponible après exécution agents)
  const workspacePath = (
    data?.dispatch as { workspace_path?: string } | undefined
  )?.workspace_path;
  const engineeringSpec = (
    data?.package as { engineering_spec?: { task_breakdown?: unknown[] } } | undefined
  )?.engineering_spec;
  const taskCount = engineeringSpec?.task_breakdown?.length ?? 0;
  const canPrdEngineering = Boolean(data?.package);

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-6 pb-4">
      <div>
        <div className="mb-2 flex items-center gap-2">
          <Crown className="h-5 w-5 text-copper" />
          <h2 className="font-title text-xl text-ivory">Dossier CEO & dispatch</h2>
        </div>
        <p className="text-sm leading-relaxed text-titanium/70">
          Package exécutif pour{" "}
          <span className="text-ivory/90">{dossierTitle}</span> — templates par branche,
          CR comité structuré, matrice dispatch. Le{" "}
          <strong className="font-normal text-ivory/85">COO intervient après</strong> ta
          validation, pas en salle de réunion R&D.
        </p>
      </div>

      {loading ? (
        <div className="flex h-32 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-copper/40" />
        </div>
      ) : (
        <>
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="rounded-full border border-white/10 px-2 py-0.5 text-titanium/60">
              Dossier : {dossierStatus}
            </span>
            <span className="rounded-full border border-white/10 px-2 py-0.5 text-titanium/60">
              CEO : {data?.ceo_status ?? "pending"}
            </span>
            <span className="rounded-full border border-white/10 px-2 py-0.5 text-titanium/60">
              Dispatch : {STATUS_LABELS[data?.dispatch_status ?? "pending"] ?? data?.dispatch_status}
            </span>
            {recommendation ? (
              <span
                className={cn(
                  "rounded-full border px-2 py-0.5 font-medium",
                  recommendation === "GO"
                    ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-300"
                    : recommendation === "NO"
                      ? "border-red-500/30 bg-red-500/10 text-red-300"
                      : "border-amber-500/30 bg-amber-500/10 text-amber-200"
                )}
              >
                Recommandation comité : {recommendation}
              </span>
            ) : null}
          </div>

          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              onClick={() => handleGenerate(Boolean(data?.package))}
              disabled={!data?.can_generate || generating}
              className="bg-copper text-obsidian hover:bg-copper/90"
            >
              {generating ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : data?.package ? (
                <RotateCcw className="mr-2 h-4 w-4" />
              ) : (
                <Crown className="mr-2 h-4 w-4" />
              )}
              {data?.package ? "Regénérer dossier CEO" : "Générer dossier CEO"}
            </Button>
            {data?.can_dispatch ? (
              <Button
                type="button"
                variant="outline"
                className="border-copper/35 text-copper hover:bg-copper/10"
                onClick={handleDispatch}
                disabled={dispatching}
              >
                {dispatching ? (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                ) : (
                  <Send className="mr-2 h-4 w-4" />
                )}
                Dispatcher au COO
              </Button>
            ) : null}
            {data?.dispatch_status === "dispatched" ? (
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="outline"
                  className="border-emerald-500/35 text-emerald-200"
                  onClick={handleExecuteAgents}
                  disabled={executing || executionStatus === "running"}
                >
                  {executing || executionStatus === "running" ? (
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  ) : (
                    <Rocket className="mr-2 h-4 w-4" />
                  )}
                  {executionStatus === "running" ? "Agents en cours…" : "Lancer les agents"}
                </Button>
                <Button type="button" variant="outline" className="border-white/10" asChild>
                  <Link href="/openroom">OpenRoom</Link>
                </Button>
                <Button type="button" variant="outline" className="border-white/10" asChild>
                  <Link href="/roadmap">Roadmap</Link>
                </Button>
              </div>
            ) : null}
          </div>

          {canPrdEngineering ? (
            <div className="rounded-xl border border-copper/20 bg-copper/[0.04] p-4">
              <div className="mb-2 flex items-center gap-2">
                <GitBranch className="h-4 w-4 text-copper/80" />
                <span className="text-xs font-medium text-ivory/85">
                  PRD Engineering (Phase 3)
                </span>
                {taskCount > 0 ? (
                  <span className="rounded-full border border-white/10 px-2 py-0.5 text-[10px] text-titanium/60">
                    {taskCount} tâches
                  </span>
                ) : null}
              </div>
              <p className="mb-3 text-xs leading-relaxed text-titanium/65">
                Léon génère la spec technique §10 ; Sam publie les issues GitHub
                agent-ready pour le coding pipeline.
              </p>
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="border-copper/30 text-copper"
                  onClick={() => handleGenerateSpec(Boolean(engineeringSpec))}
                  disabled={generatingSpec}
                >
                  {generatingSpec ? (
                    <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                  ) : null}
                  {engineeringSpec ? "Regénérer spec §10" : "Générer spec §10"}
                </Button>
                {data?.ceo_status === "approved" ? (
                  <>
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      className="border-white/10"
                      onClick={() => handleDecomposePrd(true)}
                      disabled={decomposing || taskCount === 0}
                    >
                      Dry-run issues
                    </Button>
                    <Button
                      type="button"
                      size="sm"
                      className="bg-copper/90 text-obsidian hover:bg-copper"
                      onClick={() => handleDecomposePrd(false)}
                      disabled={decomposing || taskCount === 0}
                    >
                      {decomposing ? (
                        <Loader2 className="mr-2 h-3 w-3 animate-spin" />
                      ) : (
                        <GitBranch className="mr-2 h-3 w-3" />
                      )}
                      Publier issues GitHub
                    </Button>
                  </>
                ) : (
                  <span className="self-center text-[10px] text-titanium/50">
                    Valide le dossier CEO pour publier les issues
                  </span>
                )}
              </div>
            </div>
          ) : null}

          {/* Item 6 — Workspace path + bouton Ouvrir dossier */}
          {data?.dispatch_status === "dispatched" && workspacePath ? (
            <div className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
              <div className="mb-2 flex items-center gap-2">
                <FolderOpen className="h-4 w-4 text-copper/70" />
                <span className="text-xs font-medium text-ivory/80">Workspace disque</span>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <code className="flex-1 rounded bg-white/[0.04] px-3 py-1.5 font-mono text-[11px] text-titanium/70 break-all">
                  {workspacePath}
                </code>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="shrink-0 border-white/10 text-xs"
                  onClick={() => {
                    void navigator.clipboard.writeText(workspacePath);
                    toast.success("Chemin copié");
                  }}
                >
                  Copier chemin
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="shrink-0 border-copper/30 text-xs text-copper"
                  onClick={() => {
                    // Ouvre dans VS Code / Cursor (vscode://) ou fallback file://
                    const uri = `vscode://file/${workspacePath.replace(/\\/g, "/")}`;
                    window.open(uri, "_blank");
                  }}
                >
                  <FolderOpen className="mr-1 h-3 w-3" />
                  Ouvrir dossier
                </Button>
              </div>
              <p className="mt-2 text-[10px] text-titanium/45">
                Convention : ALNUA/&#123;pole&#125;/&#123;slug&#125;/&#123;livrable&#125;
              </p>
            </div>
          ) : null}

          {!data?.can_generate && !data?.package ? (
            <p className="rounded-xl border border-amber-500/20 bg-amber-500/[0.06] p-4 text-xs text-titanium/70">
              Termine le comité R&D (statut partial_validated ou ready_for_ceo) avant de
              générer le package CEO.
            </p>
          ) : null}

          {data?.can_decide ? (
            <div className="rounded-xl border border-copper/20 bg-white/[0.02] p-4">
              <p className="mb-3 text-sm font-medium text-ivory/90">Validation CEO</p>
              {showNote ? (
                <Textarea
                  value={ceoNote}
                  onChange={(e) => setCeoNote(e.target.value)}
                  placeholder="Note optionnelle (pivot, conditions, next steps)…"
                  rows={3}
                  className="mb-3 border-copper/15 bg-white/[0.02] text-sm"
                />
              ) : (
                <button
                  type="button"
                  onClick={() => setShowNote(true)}
                  className="mb-3 text-xs text-copper hover:underline"
                >
                  + Ajouter une note
                </button>
              )}
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  size="sm"
                  className="bg-emerald-600 hover:bg-emerald-600/90"
                  disabled={!!deciding}
                  onClick={() => handleDecide("approved")}
                >
                  {deciding === "approved" ? (
                    <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                  ) : (
                    <CheckCircle2 className="mr-1 h-3 w-3" />
                  )}
                  Approuver (GO)
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="border-amber-500/35 text-amber-200"
                  disabled={!!deciding}
                  onClick={() => handleDecide("pivot_requested")}
                >
                  {deciding === "pivot_requested" ? (
                    <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                  ) : (
                    <RotateCcw className="mr-1 h-3 w-3" />
                  )}
                  Pivot (MAYBE)
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="border-red-500/35 text-red-300"
                  disabled={!!deciding}
                  onClick={() => handleDecide("rejected")}
                >
                  {deciding === "rejected" ? (
                    <Loader2 className="mr-1 h-3 w-3 animate-spin" />
                  ) : (
                    <XCircle className="mr-1 h-3 w-3" />
                  )}
                  Rejeter (NO)
                </Button>
              </div>
            </div>
          ) : null}

          {data?.ceo_status === "approved" && data.dispatch_status !== "dispatched" ? (
            <div className="rounded-xl border border-emerald-500/20 bg-emerald-500/[0.06] p-4 text-xs text-titanium/75">
              <Rocket className="mb-1 inline h-3.5 w-3.5 text-emerald-300" /> Projet approuvé —
              lance le dispatch COO pour créer les entrées roadmap par pôle. Pipeline social
              débloqué dans l&apos;onglet Social.
            </div>
          ) : null}

          {matrix.length > 0 ? (
            <div>
              <h3 className="mb-2 text-sm font-medium text-ivory/85">Matrice dispatch</h3>
              <ul className="space-y-2">
                {matrix.map((row) => (
                  <li
                    key={`${row.agent_id}-${row.pole}`}
                    className="rounded-lg border border-white/8 bg-white/[0.02] px-3 py-2 text-xs"
                  >
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-medium text-ivory/90">{row.pole}</span>
                      <span className="text-titanium/50">{row.agent_id}</span>
                    </div>
                    <p className="mt-1 text-titanium/60">
                      {row.deliverables.join(" · ")}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {markdown ? (
            <div className="rounded-xl border border-copper/15 bg-white/[0.02] p-5">
              <h3 className="mb-3 text-sm font-medium text-ivory/85">Package CEO (aperçu)</h3>
              <MarkdownContent className="prose-sm max-w-none text-titanium/85">
                {markdown.length > 12000
                  ? `${markdown.slice(0, 12000)}\n\n_… document tronqué dans l'aperçu_`
                  : markdown}
              </MarkdownContent>
            </div>
          ) : (
            <div className="rounded-xl border border-copper/15 bg-white/[0.02] p-8 text-center text-sm text-titanium/60">
              Aucun dossier CEO — génère le package après clôture du comité.
            </div>
          )}
        </>
      )}
    </div>
  );
}
