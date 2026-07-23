"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  FolderPlus,
  GitBranchPlus,
  Loader2,
  Play,
  RefreshCw,
  Scissors,
  Sparkles,
  Star,
  TreePine,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { RndHypothesisTreeGraph } from "@/components/rnd/rnd-hypothesis-tree-graph";
import {
  expandRndNode,
  fetchLatestLlmBenchmark,
  fetchRndTree,
  fetchRndTreeGraph,
  fetchRndTrees,
  fetchRndWatchTopics,
  patchRndNodeStatus,
  promoteRndNode,
  runLlmLatencyBenchmark,
  runRndNode,
  startRndInvestigation,
  type HypothesisNode,
  type LlmBenchmarkResult,
  type RndTreeDetail,
  type RndTreeGraph,
  type RndTreeSummary,
  type RndWatchTopic,
} from "@/lib/rnd-tree-api";
import { rdDossierHref } from "@/lib/routes";

interface RndHypothesisTreePanelProps {
  initialSlug?: string | null;
  onDossierCreated?: (dossierId: string) => void;
}

export function RndHypothesisTreePanel({
  initialSlug,
  onDossierCreated,
}: RndHypothesisTreePanelProps) {
  const [trees, setTrees] = useState<RndTreeSummary[]>([]);
  const [selectedSlug, setSelectedSlug] = useState<string | null>(initialSlug ?? null);
  const [treeDetail, setTreeDetail] = useState<RndTreeDetail | null>(null);
  const [graph, setGraph] = useState<RndTreeGraph | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [watchTopics, setWatchTopics] = useState<RndWatchTopic[]>([]);
  const [benchmark, setBenchmark] = useState<LlmBenchmarkResult | null>(null);
  const [topic, setTopic] = useState("");
  const [manualTitle, setManualTitle] = useState("");
  const [manualHypothesis, setManualHypothesis] = useState("");
  const [loading, setLoading] = useState(true);
  const [launching, setLaunching] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  const [benchmarking, setBenchmarking] = useState(false);

  const selectedNode: HypothesisNode | undefined = treeDetail?.nodes.find(
    (n) => n.id === selectedNodeId
  );

  const loadTrees = useCallback(async () => {
    try {
      const [treesRes, watchRes, benchRes] = await Promise.all([
        fetchRndTrees(),
        fetchRndWatchTopics(),
        fetchLatestLlmBenchmark(),
      ]);
      setTrees(treesRes.trees);
      setWatchTopics(watchRes.topics);
      setBenchmark(benchRes.benchmark);
    } catch {
      // Hub down
    }
  }, []);

  const loadDetail = useCallback(async (slug: string, pickRoot = false) => {
    try {
      const [detail, graphData] = await Promise.all([
        fetchRndTree(slug),
        fetchRndTreeGraph(slug),
      ]);
      setTreeDetail(detail);
      setGraph(graphData);
      if (pickRoot && detail.root_id) {
        setSelectedNodeId(detail.root_id);
      }
    } catch {
      setTreeDetail(null);
      setGraph(null);
    }
  }, []);

  const load = useCallback(async () => {
    setLoading(true);
    await loadTrees();
    if (selectedSlug) {
      await loadDetail(selectedSlug);
    }
    setLoading(false);
  }, [loadTrees, loadDetail, selectedSlug]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!selectedSlug) return;
    const active = treeDetail?.status === "active";
    if (!active && treeDetail?.status === "completed") return;
    const interval = window.setInterval(() => {
      void loadDetail(selectedSlug);
      void loadTrees();
    }, active ? 12_000 : 60_000);
    return () => window.clearInterval(interval);
  }, [selectedSlug, treeDetail?.status, loadDetail, loadTrees]);

  async function handleLaunch(e: React.FormEvent) {
    e.preventDefault();
    const q = topic.trim();
    if (q.length < 3) {
      toast.error("Saisis au moins 3 caractères");
      return;
    }
    setLaunching(true);
    try {
      const res = await startRndInvestigation(q);
      toast.success(res.message ?? "Arbre lancé");
      setTopic("");
      setSelectedSlug(res.slug);
      await loadTrees();
      await loadDetail(res.slug, true);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Échec du lancement");
    } finally {
      setLaunching(false);
    }
  }

  async function handleExpand(auto: boolean) {
    if (!selectedSlug || !selectedNodeId) return;
    setActionLoading(true);
    try {
      const res = await expandRndNode(selectedSlug, selectedNodeId, {
        maxChildren: 3,
        runAfter: auto,
        title: auto ? undefined : manualTitle.trim() || undefined,
        hypothesis: auto ? undefined : manualHypothesis.trim() || undefined,
      });
      toast.success(`${res.children_created} branche(s) créée(s)`);
      setManualTitle("");
      setManualHypothesis("");
      await loadDetail(selectedSlug);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Expansion échouée");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleRunNode() {
    if (!selectedSlug || !selectedNodeId) return;
    setActionLoading(true);
    try {
      await runRndNode(selectedSlug, selectedNodeId);
      toast.success("Investigation lancée sur la branche");
      await loadDetail(selectedSlug);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setActionLoading(false);
    }
  }

  async function handlePromote() {
    if (!selectedSlug || !selectedNodeId) return;
    setActionLoading(true);
    try {
      const res = await promoteRndNode(selectedSlug, selectedNodeId);
      toast.success(res.message ?? "Dossier créé");
      if (res.dossier_id && onDossierCreated) {
        onDossierCreated(res.dossier_id);
      }
      await loadDetail(selectedSlug);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Promotion échouée");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleStatus(status: "merged" | "pruned" | "explored") {
    if (!selectedSlug || !selectedNodeId) return;
    setActionLoading(true);
    try {
      await patchRndNodeStatus(selectedSlug, selectedNodeId, status);
      toast.success(`Branche → ${status}`);
      await loadDetail(selectedSlug);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Erreur");
    } finally {
      setActionLoading(false);
    }
  }

  async function handleBenchmark() {
    setBenchmarking(true);
    try {
      const res = await runLlmLatencyBenchmark();
      setBenchmark(res);
      toast.success("Benchmark terminé");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Benchmark échoué");
    } finally {
      setBenchmarking(false);
    }
  }

  function launchWatchTopic(w: RndWatchTopic) {
    setTopic(`recherche R&D ${w.title.split("(")[0].trim()}`);
  }

  return (
    <div className="flex h-full flex-col gap-4 overflow-hidden">
      <div className="flex shrink-0 items-center gap-2">
        <TreePine className="h-5 w-5 text-emerald-400/80" />
        <div>
          <h3 className="text-sm font-semibold text-ivory/90">Arbres d&apos;hypothèses</h3>
          <p className="text-[11px] text-titanium/55">
            Phase 2 — graphe interactif · expansion manuelle · promote dossier
          </p>
        </div>
        <Button
          type="button"
          size="icon"
          variant="ghost"
          className="ml-auto h-8 w-8"
          onClick={() => void load()}
          aria-label="Rafraîchir"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      <form onSubmit={(e) => void handleLaunch(e)} className="flex shrink-0 gap-2">
        <Input
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="Ex. robotique, DiffusionGemma pour Nadia PC…"
          className="border-copper/20 bg-obsidian-deep/70 text-sm"
          disabled={launching}
        />
        <Button
          type="submit"
          disabled={launching}
          className="shrink-0 bg-emerald-600 text-white hover:bg-emerald-500"
        >
          {launching ? <Loader2 className="h-4 w-4 animate-spin" /> : (
            <><Play className="mr-1 h-3.5 w-3.5" />Lancer</>
          )}
        </Button>
      </form>

      {watchTopics.length > 0 ? (
        <div className="shrink-0 space-y-2">
          <div className="flex items-center justify-between">
            <p className="text-[11px] font-medium uppercase tracking-wide text-titanium/50">
              Veille R&D
            </p>
            <Button
              type="button"
              size="sm"
              variant="outline"
              disabled={benchmarking}
              className="h-7 border-violet-500/30 text-[11px] text-violet-300"
              onClick={() => void handleBenchmark()}
            >
              {benchmarking ? (
                <Loader2 className="mr-1 h-3 w-3 animate-spin" />
              ) : (
                <Zap className="mr-1 h-3 w-3" />
              )}
              Benchmark latence
            </Button>
          </div>
          <div className="grid gap-2 sm:grid-cols-2">
            {watchTopics.map((w) => (
              <button
                key={w.id}
                type="button"
                className="rounded-lg border border-violet-500/20 bg-violet-500/5 p-3 text-left transition hover:opacity-90"
                onClick={() => launchWatchTopic(w)}
              >
                <div className="flex items-center gap-2">
                  <Sparkles className="h-3.5 w-3.5 text-violet-300" />
                  <p className="text-sm font-medium text-ivory/90">{w.title}</p>
                </div>
                <p className="mt-1 line-clamp-2 text-xs text-titanium/70">{w.summary}</p>
              </button>
            ))}
          </div>
          {benchmark ? (
            <div className="rounded-lg border border-white/10 bg-obsidian-deep/70 p-3 text-xs text-titanium/75">
              <p className="font-medium text-ivory/85">
                OpenRouter ~{benchmark.openrouter.avg_elapsed_ms ?? "?"} ms ·{" "}
                ~{benchmark.openrouter.avg_tokens_per_second ?? "?"} tok/s
              </p>
              <p className="mt-1">
                DiffusionGemma (réf. RTX 5090) : ~
                {benchmark.diffusion_gemma_reference.published_tokens_per_second_rtx5090} tok/s
                {benchmark.comparison.diffusion_gemma_estimated_speedup_vs_openrouter
                  ? ` · ~${benchmark.comparison.diffusion_gemma_estimated_speedup_vs_openrouter}× plus rapide`
                  : ""}
              </p>
              <p className="mt-1 text-[11px] text-titanium/55">{benchmark.recommendation}</p>
            </div>
          ) : null}
        </div>
      ) : null}

      <div className="grid min-h-0 flex-1 gap-3 lg:grid-cols-[180px_1fr_260px]">
        <div className="flex min-h-0 flex-col gap-1 overflow-y-auto rounded-xl border border-white/10 bg-obsidian-deep/50 p-2">
          <p className="px-1 text-[10px] font-medium uppercase text-titanium/45">Historique</p>
          {trees.length === 0 ? (
            <p className="px-1 py-4 text-xs text-titanium/50">Aucun arbre.</p>
          ) : (
            trees.map((t) => (
              <button
                key={t.slug}
                type="button"
                onClick={() => {
                  setSelectedSlug(t.slug);
                  setSelectedNodeId(null);
                  void loadDetail(t.slug, true);
                }}
                className={`rounded-lg px-2 py-2 text-left text-xs transition ${
                  selectedSlug === t.slug
                    ? "bg-copper/15 text-ivory"
                    : "text-titanium/70 hover:bg-white/[0.04]"
                }`}
              >
                <p className="line-clamp-2 font-medium">{t.topic}</p>
                <p className="mt-0.5 text-[10px] opacity-60">
                  {t.status} · ★{t.merged_count}
                </p>
              </button>
            ))
          )}
        </div>

        <div className="flex min-h-0 flex-col gap-2 overflow-hidden">
          {!graph ? (
            <p className="py-8 text-center text-sm text-titanium/50">
              Sélectionne un arbre.
            </p>
          ) : (
            <>
              <p className="shrink-0 text-sm font-semibold text-ivory/90">{graph.topic}</p>
              <div className="min-h-0 flex-1">
                <RndHypothesisTreeGraph
                  nodes={graph.nodes}
                  edges={graph.edges}
                  width={graph.width}
                  height={graph.height}
                  selectedId={selectedNodeId}
                  onSelect={setSelectedNodeId}
                />
              </div>
            </>
          )}
        </div>

        <div className="flex min-h-0 flex-col gap-2 overflow-y-auto rounded-xl border border-white/10 bg-obsidian-deep/50 p-3">
          <p className="text-[10px] font-medium uppercase text-titanium/45">Branche sélectionnée</p>
          {!selectedNode ? (
            <p className="text-xs text-titanium/50">Clique un nœud du graphe.</p>
          ) : (
            <>
              <div>
                <p className="text-sm font-medium text-ivory/90">{selectedNode.title}</p>
                <p className="mt-1 text-[11px] text-titanium/60">{selectedNode.status}</p>
                {selectedNode.score != null ? (
                  <p className="text-[11px] text-titanium/55">
                    {selectedNode.score}/30 · {selectedNode.verdict}
                  </p>
                ) : null}
                <p className="mt-2 text-xs leading-relaxed text-titanium/70">
                  {selectedNode.hypothesis}
                </p>
                {selectedNode.insight ? (
                  <p className="mt-2 text-xs italic text-titanium/55">💡 {selectedNode.insight}</p>
                ) : null}
              </div>

              <div className="flex flex-wrap gap-1.5">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={actionLoading}
                  className="h-8 text-[11px]"
                  onClick={() => void handleRunNode()}
                >
                  <Play className="mr-1 h-3 w-3" />
                  Investiguer
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={actionLoading}
                  className="h-8 text-[11px]"
                  onClick={() => void handleExpand(true)}
                >
                  <GitBranchPlus className="mr-1 h-3 w-3" />
                  +3 branches IA
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  disabled={actionLoading}
                  className="h-8 text-[11px] border-emerald-500/30 text-emerald-300"
                  onClick={() => void handlePromote()}
                >
                  <FolderPlus className="mr-1 h-3 w-3" />
                  Dossier
                </Button>
              </div>

              <div className="flex gap-1.5">
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={actionLoading}
                  className="h-7 text-[10px] text-emerald-400"
                  onClick={() => void handleStatus("merged")}
                >
                  <Star className="mr-1 h-3 w-3" />
                  Merger
                </Button>
                <Button
                  size="sm"
                  variant="ghost"
                  disabled={actionLoading}
                  className="h-7 text-[10px] text-red-400"
                  onClick={() => void handleStatus("pruned")}
                >
                  <Scissors className="mr-1 h-3 w-3" />
                  Pruner
                </Button>
              </div>

              {selectedNode.dossier_id ? (
                <Link
                  href={rdDossierHref(selectedNode.dossier_id)}
                  className="text-[11px] text-copper hover:underline"
                >
                  Ouvrir le dossier →
                </Link>
              ) : null}

              <div className="space-y-1.5 border-t border-white/10 pt-2">
                <p className="text-[10px] text-titanium/45">Branche manuelle</p>
                <Input
                  value={manualTitle}
                  onChange={(e) => setManualTitle(e.target.value)}
                  placeholder="Titre"
                  className="h-8 border-white/10 bg-obsidian-deep/70 text-xs"
                />
                <Textarea
                  value={manualHypothesis}
                  onChange={(e) => setManualHypothesis(e.target.value)}
                  placeholder="Hypothèse à tester"
                  rows={2}
                  className="resize-none border-white/10 bg-obsidian-deep/70 text-xs"
                />
                <Button
                  size="sm"
                  variant="outline"
                  disabled={actionLoading || !manualTitle.trim()}
                  className="h-8 w-full text-[11px]"
                  onClick={() => void handleExpand(false)}
                >
                  Ajouter branche
                </Button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
