"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import {
  expandRndNode,
  fetchRndTree,
  fetchRndTreeGraph,
  fetchRndTrees,
  patchRndNodeStatus,
  promoteRndNode,
  reparentRndNode,
  runRndNode,
  startRndInvestigation,
  type GraphNode,
  type HypothesisNode,
  type HypothesisNodeStatus,
  type RndTreeDetail,
  type RndTreeGraph,
  type RndTreeSummary,
} from "@/lib/rnd-tree-api";
import { MarkdownContent } from "@/components/shared/markdown-content";
import { C } from "../app-v2/shared";

/* Arbres (Phase 26, ROADMAP.md) — canvas mindmap glissable, remplace l'ancien
   rendu SVG statique (rnd-hypothesis-tree-graph.tsx, onClick uniquement).
   Backend déjà réel (services/rnd_hypothesis_tree.py) : "créer" une branche
   = expand_node(manual=...) (déjà existant), "fusionner/promouvoir" =
   promote_node_to_dossier (déjà existant, positionne status="merged"),
   "relier" (glisser un nœud sur un autre) nécessitait un vrai ajout backend
   — reparent_node() + PATCH .../reparent — car l'arbre était strictement
   parent/enfant sans re-parentage. Les positions ne sont JAMAIS persistées
   côté serveur (build_tree_graph recalcule un layout BFS à chaque appel) :
   déplacer un nœud sans le lâcher sur un autre est donc un repositionnement
   purement visuel, local à la session — seul le "relier" (dépôt sur un
   autre nœud) déclenche une vraie mutation. */

const NODE_W = 176;
const NODE_H = 68;
const DROP_THRESHOLD = 92;

const STATUS_META: Record<HypothesisNodeStatus, { label: string; color: string; bg: string }> = {
  pending: { label: "En attente", color: "#A7ADB5", bg: "rgba(113,113,122,.16)" },
  running: { label: "En cours", color: "#60a5fa", bg: "rgba(29,78,216,.18)" },
  explored: { label: "Exploré", color: "#fbbf24", bg: "rgba(180,83,9,.18)" },
  merged: { label: "Fusionné", color: "#34d399", bg: "rgba(5,150,105,.18)" },
  pruned: { label: "Élagué", color: "#f87171", bg: "rgba(153,27,27,.18)" },
  failed: { label: "Échec", color: "#ef4444", bg: "rgba(127,29,29,.18)" },
};

interface Pos {
  x: number;
  y: number;
}

interface DragState {
  nodeId: string;
  startClient: Pos;
  startPos: Pos;
  moved: boolean;
}

export function ArbresTab() {
  const [trees, setTrees] = useState<RndTreeSummary[]>([]);
  const [slug, setSlug] = useState<string | null>(null);
  const [graph, setGraph] = useState<RndTreeGraph | null>(null);
  const [detail, setDetail] = useState<RndTreeDetail | null>(null);
  const [loadingTrees, setLoadingTrees] = useState(true);
  const [loadingGraph, setLoadingGraph] = useState(false);
  const [positions, setPositions] = useState<Record<string, Pos>>({});
  const [dragState, setDragState] = useState<DragState | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [busyNodeId, setBusyNodeId] = useState<string | null>(null);
  const [branchFormOpen, setBranchFormOpen] = useState(false);
  const [branchTitle, setBranchTitle] = useState("");
  const [branchHypothesis, setBranchHypothesis] = useState("");
  const [newTopic, setNewTopic] = useState("");
  const [launching, setLaunching] = useState(false);
  const positionsRef = useRef(positions);
  positionsRef.current = positions;

  const loadTrees = useCallback((selectSlug?: string) => {
    setLoadingTrees(true);
    fetchRndTrees(30)
      .then((res) => {
        setTrees(res.trees);
        setSlug((prev) => selectSlug ?? prev ?? res.trees[0]?.slug ?? null);
      })
      .catch(() => setTrees([]))
      .finally(() => setLoadingTrees(false));
  }, []);

  useEffect(() => {
    loadTrees();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadGraph = useCallback((targetSlug: string) => {
    setLoadingGraph(true);
    setSelectedId(null);
    setBranchFormOpen(false);
    Promise.all([fetchRndTreeGraph(targetSlug), fetchRndTree(targetSlug)])
      .then(([g, d]) => {
        setGraph(g);
        setDetail(d);
        const next: Record<string, Pos> = {};
        g.nodes.forEach((n) => {
          next[n.id] = { x: n.x, y: n.y };
        });
        setPositions(next);
      })
      .catch(() => {
        setGraph(null);
        setDetail(null);
      })
      .finally(() => setLoadingGraph(false));
  }, []);

  useEffect(() => {
    if (slug) loadGraph(slug);
  }, [slug, loadGraph]);

  const nodeById = useMemo(() => {
    const map = new Map<string, HypothesisNode>();
    detail?.nodes.forEach((n) => map.set(n.id, n));
    return map;
  }, [detail]);

  const selectedNode = selectedId ? (nodeById.get(selectedId) ?? null) : null;
  const selectedGraphNode = selectedId ? (graph?.nodes.find((n) => n.id === selectedId) ?? null) : null;

  function startDrag(e: React.MouseEvent, nodeId: string) {
    e.preventDefault();
    e.stopPropagation();
    setDragState({
      nodeId,
      startClient: { x: e.clientX, y: e.clientY },
      startPos: positionsRef.current[nodeId] ?? { x: 0, y: 0 },
      moved: false,
    });
  }

  useEffect(() => {
    if (!dragState) return;
    const active = dragState;

    function onMove(e: MouseEvent) {
      const dx = e.clientX - active.startClient.x;
      const dy = e.clientY - active.startClient.y;
      if (!active.moved && Math.hypot(dx, dy) > 4) active.moved = true;
      setPositions((prev) => ({
        ...prev,
        [active.nodeId]: { x: active.startPos.x + dx, y: active.startPos.y + dy },
      }));
    }

    function onUp(e: MouseEvent) {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
      setDragState(null);

      if (!active.moved) {
        setSelectedId(active.nodeId);
        return;
      }
      if (!slug || !graph) return;

      const dx = e.clientX - active.startClient.x;
      const dy = e.clientY - active.startClient.y;
      const dropX = active.startPos.x + dx;
      const dropY = active.startPos.y + dy;

      let target: GraphNode | null = null;
      let bestDist = DROP_THRESHOLD;
      for (const n of graph.nodes) {
        if (n.id === active.nodeId) continue;
        const p = positionsRef.current[n.id] ?? { x: n.x, y: n.y };
        const dist = Math.hypot(p.x - dropX, p.y - dropY);
        if (dist < bestDist) {
          bestDist = dist;
          target = n;
        }
      }

      if (target) {
        const targetTitle = target.title;
        setBusyNodeId(active.nodeId);
        reparentRndNode(slug, active.nodeId, target.id)
          .then(() => {
            toast.success(`Relié à « ${targetTitle} ».`);
          })
          .catch((err) => {
            toast.error(err instanceof Error ? err.message : "Impossible de relier ce nœud");
          })
          .finally(() => {
            setBusyNodeId(null);
            loadGraph(slug);
          });
      }
      // Sinon : simple repositionnement visuel, non persisté côté serveur.
    }

    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [dragState, slug, graph, loadGraph]);

  async function handleExplore(nodeId: string) {
    if (!slug) return;
    setBusyNodeId(nodeId);
    try {
      const res = await runRndNode(slug, nodeId);
      toast.success(res.status === "running" ? "Déjà en cours d'exploration." : "Exploration lancée.");
      loadGraph(slug);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Échec du lancement de l'exploration");
    } finally {
      setBusyNodeId(null);
    }
  }

  async function handlePrune(nodeId: string) {
    if (!slug) return;
    setBusyNodeId(nodeId);
    try {
      await patchRndNodeStatus(slug, nodeId, "pruned");
      toast.success("Branche élaguée.");
      loadGraph(slug);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Échec de l'élagage");
    } finally {
      setBusyNodeId(null);
    }
  }

  async function handlePromote(nodeId: string) {
    if (!slug) return;
    setBusyNodeId(nodeId);
    try {
      const res = await promoteRndNode(slug, nodeId);
      toast.success(res.already ? "Dossier déjà créé pour cette branche." : "Fusionné — dossier R&D créé.");
      loadGraph(slug);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Échec de la fusion en dossier");
    } finally {
      setBusyNodeId(null);
    }
  }

  async function handleAddBranch(nodeId: string) {
    if (!slug || !branchTitle.trim()) return;
    setBusyNodeId(nodeId);
    try {
      await expandRndNode(slug, nodeId, {
        title: branchTitle.trim(),
        hypothesis: branchHypothesis.trim() || undefined,
      });
      toast.success("Nouvelle branche créée.");
      setBranchFormOpen(false);
      setBranchTitle("");
      setBranchHypothesis("");
      loadGraph(slug);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Échec de la création de branche");
    } finally {
      setBusyNodeId(null);
    }
  }

  async function handleLaunchInvestigation() {
    if (!newTopic.trim()) return;
    setLaunching(true);
    try {
      const res = await startRndInvestigation(newTopic.trim());
      toast.success(res.message || "Investigation lancée (~3-8 min).");
      setNewTopic("");
      loadTrees(res.slug);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Échec du lancement de l'investigation");
    } finally {
      setLaunching(false);
    }
  }

  const containerWidth = graph ? graph.width + NODE_W + 40 : 0;
  const containerHeight = graph ? graph.height + NODE_H + 40 : 0;
  const offsetX = containerWidth / 2;
  const offsetY = 20;

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-hidden pb-2">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2">
          <p className="shrink-0 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            ARBRES
          </p>
          {loadingTrees ? (
            <Loader2 className="h-3 w-3 animate-spin" style={{ color: C.faint }} />
          ) : trees.length === 0 ? (
            <span className="text-[10.5px]" style={{ color: C.faint }}>
              Aucun arbre d&apos;hypothèses pour le moment.
            </span>
          ) : (
            <select
              value={slug ?? ""}
              onChange={(e) => setSlug(e.target.value)}
              className="max-w-[320px] truncate rounded-lg border bg-transparent px-2 py-1 text-[11px]"
              style={{ borderColor: C.lineSoft, color: C.ivory }}
            >
              {trees.map((t) => (
                <option key={t.slug} value={t.slug} style={{ background: "#16130f" }}>
                  {t.topic} · {t.node_count} nœuds{t.status === "active" ? " · actif" : ""}
                </option>
              ))}
            </select>
          )}
          {slug ? (
            <button
              type="button"
              onClick={() => loadGraph(slug)}
              title="Rafraîchir"
              className="rounded-lg border px-2 py-1 text-[10px]"
              style={{ borderColor: C.lineSoft, color: C.warm }}
            >
              🔄
            </button>
          ) : null}
        </div>

        <div className="flex items-center gap-1.5">
          <input
            value={newTopic}
            onChange={(e) => setNewTopic(e.target.value)}
            placeholder="Nouveau thème à investiguer…"
            className="w-[200px] rounded-lg border bg-transparent px-2.5 py-1 text-[10.5px] outline-none"
            style={{ borderColor: C.lineSoft, color: C.ivory }}
          />
          <button
            type="button"
            disabled={launching || !newTopic.trim()}
            onClick={() => void handleLaunchInvestigation()}
            className="flex items-center gap-1 rounded-lg border px-2.5 py-1 text-[10.5px] disabled:opacity-50"
            style={{ borderColor: "rgba(192,138,114,.4)", background: "rgba(192,138,114,.1)", color: C.copperLight }}
          >
            {launching ? <Loader2 className="h-3 w-3 animate-spin" /> : "🌱"} Investiguer
          </button>
        </div>
      </div>

      <div className="flex min-h-0 flex-1 gap-3">
        {/* Canvas */}
        <div
          className="alnua-scroll relative min-w-0 flex-1 overflow-auto rounded-xl border"
          style={{ borderColor: C.line, background: "rgba(10,8,7,.5)" }}
        >
          {loadingGraph ? (
            <div className="flex h-full min-h-[300px] items-center justify-center text-[11px]" style={{ color: C.faint }}>
              Chargement de l&apos;arbre…
            </div>
          ) : !graph ? (
            <div className="flex h-full min-h-[300px] items-center justify-center text-[11px]" style={{ color: C.faint }}>
              Sélectionnez ou lancez un arbre d&apos;hypothèses.
            </div>
          ) : (
            <div className="relative" style={{ width: containerWidth, height: containerHeight }}>
              <svg className="pointer-events-none absolute inset-0" width={containerWidth} height={containerHeight}>
                {graph.edges.map((e) => {
                  const from = positions[e.from] ?? graph.nodes.find((n) => n.id === e.from);
                  const to = positions[e.to] ?? graph.nodes.find((n) => n.id === e.to);
                  if (!from || !to) return null;
                  const x1 = offsetX + from.x;
                  const y1 = offsetY + from.y + NODE_H;
                  const x2 = offsetX + to.x;
                  const y2 = offsetY + to.y;
                  const midY = (y1 + y2) / 2;
                  return (
                    <path
                      key={`${e.from}-${e.to}`}
                      d={`M ${x1} ${y1} C ${x1} ${midY}, ${x2} ${midY}, ${x2} ${y2}`}
                      stroke={C.lineStrong}
                      strokeWidth={1.5}
                      fill="none"
                    />
                  );
                })}
              </svg>

              {graph.nodes.map((n) => {
                const pos = positions[n.id] ?? { x: n.x, y: n.y };
                const meta = STATUS_META[n.status];
                const isSelected = n.id === selectedId;
                const isBusy = busyNodeId === n.id;
                return (
                  <div
                    key={n.id}
                    onMouseDown={(e) => startDrag(e, n.id)}
                    className="absolute flex cursor-grab select-none flex-col gap-1 rounded-lg border px-2.5 py-2 active:cursor-grabbing"
                    style={{
                      left: offsetX + pos.x,
                      top: offsetY + pos.y,
                      width: NODE_W,
                      height: NODE_H,
                      transform: "translateX(-50%)",
                      borderColor: isSelected ? C.copper : meta.color,
                      background: isSelected ? "rgba(192,138,114,.16)" : meta.bg,
                      opacity: isBusy ? 0.55 : 1,
                      boxShadow: isSelected ? "0 0 0 2px rgba(192,138,114,.3)" : undefined,
                    }}
                  >
                    <span className="truncate text-[10.5px] font-semibold" style={{ color: C.ivory }}>
                      {n.title}
                    </span>
                    <span className="flex items-center justify-between text-[8.5px]" style={{ color: meta.color }}>
                      {meta.label}
                      {n.score != null ? <span style={{ color: C.faint }}>{n.score}/100</span> : null}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Panneau détail */}
        <div
          className="flex w-[260px] shrink-0 flex-col gap-2.5 overflow-y-auto rounded-xl border p-3"
          style={{ borderColor: C.line, background: "rgba(19,22,27,.55)" }}
        >
          {!selectedNode ? (
            <p className="text-[10.5px]" style={{ color: C.faint }}>
              Cliquez un nœud pour voir ses détails. Glissez un nœud sur un autre pour le relier (re-parenter).
            </p>
          ) : (
            <>
              <div className="flex items-start justify-between gap-2">
                <p className="min-w-0 flex-1 text-[12.5px] font-semibold" style={{ color: C.ivory }}>
                  {selectedNode.title}
                </p>
                <button type="button" onClick={() => setSelectedId(null)} className="shrink-0 text-[11px]" style={{ color: C.faint }}>
                  ✕
                </button>
              </div>
              <span
                className="w-fit rounded-full border px-2 py-0.5 text-[9px]"
                style={{
                  borderColor: STATUS_META[selectedNode.status].color,
                  color: STATUS_META[selectedNode.status].color,
                }}
              >
                {STATUS_META[selectedNode.status].label}
                {selectedNode.verdict ? ` · ${selectedNode.verdict}` : ""}
                {selectedGraphNode?.score != null ? ` · ${selectedGraphNode.score}/100` : ""}
              </span>

              <p className="text-[10.5px] leading-relaxed" style={{ color: C.warm }}>
                {selectedNode.hypothesis || "—"}
              </p>

              {selectedNode.insight ? (
                <div className="rounded-md border p-2" style={{ borderColor: C.lineSoft }}>
                  <p className="mb-1 text-[8.5px] tracking-wide" style={{ color: C.faint }}>
                    INSIGHT
                  </p>
                  <p className="text-[10px]" style={{ color: C.dim }}>
                    {selectedNode.insight}
                  </p>
                </div>
              ) : null}

              {selectedNode.evidence?.key_findings?.length ? (
                <div>
                  <p className="mb-1 text-[8.5px] tracking-wide" style={{ color: C.faint }}>
                    FINDINGS
                  </p>
                  <ul className="flex flex-col gap-1">
                    {selectedNode.evidence.key_findings.map((f, i) => (
                      <li key={i} className="text-[10px]" style={{ color: C.dim }}>
                        {f.finding}
                        {f.confidence ? (
                          <span className="ml-1 text-[9px]" style={{ color: C.faint }}>
                            ({f.confidence})
                          </span>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {selectedNode.evidence?.recommended_actions?.length ? (
                <div>
                  <p className="mb-1 text-[8.5px] tracking-wide" style={{ color: C.faint }}>
                    ACTIONS RECOMMANDÉES
                  </p>
                  <ul className="list-disc space-y-0.5 pl-3.5 text-[10px]" style={{ color: C.dim }}>
                    {selectedNode.evidence.recommended_actions.map((a, i) => (
                      <li key={i}>{a}</li>
                    ))}
                  </ul>
                </div>
              ) : null}

              {selectedNode.report_markdown ? (
                <div className="rounded-md border p-2 text-[10px]" style={{ borderColor: C.lineSoft, color: C.dim }}>
                  <MarkdownContent>{selectedNode.report_markdown}</MarkdownContent>
                </div>
              ) : null}

              {selectedNode.dossier_id ? (
                <span className="text-[9.5px]" style={{ color: "#34d399" }}>
                  ✓ Dossier R&D créé
                </span>
              ) : null}

              <div className="mt-1 flex flex-col gap-1.5 border-t pt-2.5" style={{ borderColor: C.lineSoft }}>
                <button
                  type="button"
                  disabled={busyNodeId === selectedNode.id || selectedNode.status === "running"}
                  onClick={() => void handleExplore(selectedNode.id)}
                  className="rounded-lg border py-1.5 text-[10.5px] disabled:opacity-40"
                  style={{ borderColor: C.lineSoft, color: C.warm }}
                >
                  ▶ Explorer ce nœud
                </button>
                <button
                  type="button"
                  disabled={busyNodeId === selectedNode.id}
                  onClick={() => setBranchFormOpen((v) => !v)}
                  className="rounded-lg border py-1.5 text-[10.5px] disabled:opacity-40"
                  style={{ borderColor: C.lineSoft, color: C.warm }}
                >
                  + Ajouter une branche
                </button>
                {branchFormOpen ? (
                  <div className="flex flex-col gap-1.5 rounded-md border p-2" style={{ borderColor: C.lineSoft }}>
                    <input
                      value={branchTitle}
                      onChange={(e) => setBranchTitle(e.target.value)}
                      placeholder="Titre de la branche"
                      className="rounded-md border bg-transparent px-2 py-1 text-[10px] outline-none"
                      style={{ borderColor: C.lineSoft, color: C.ivory }}
                    />
                    <textarea
                      value={branchHypothesis}
                      onChange={(e) => setBranchHypothesis(e.target.value)}
                      placeholder="Hypothèse (optionnel)"
                      rows={2}
                      className="resize-none rounded-md border bg-transparent px-2 py-1 text-[10px] outline-none"
                      style={{ borderColor: C.lineSoft, color: C.ivory }}
                    />
                    <button
                      type="button"
                      disabled={!branchTitle.trim() || busyNodeId === selectedNode.id}
                      onClick={() => void handleAddBranch(selectedNode.id)}
                      className="rounded-md border py-1 text-[10px] disabled:opacity-40"
                      style={{ borderColor: "rgba(192,138,114,.4)", background: "rgba(192,138,114,.1)", color: C.copperLight }}
                    >
                      Créer la branche
                    </button>
                  </div>
                ) : null}
                <button
                  type="button"
                  disabled={busyNodeId === selectedNode.id || selectedNode.status === "pruned"}
                  onClick={() => void handlePrune(selectedNode.id)}
                  className="rounded-lg border py-1.5 text-[10.5px] disabled:opacity-40"
                  style={{ borderColor: "rgba(248,113,113,.3)", color: "#f87171" }}
                >
                  ✂ Élaguer
                </button>
                <button
                  type="button"
                  disabled={busyNodeId === selectedNode.id || !!selectedNode.dossier_id}
                  onClick={() => void handlePromote(selectedNode.id)}
                  className="rounded-lg border py-1.5 text-[10.5px] disabled:opacity-40"
                  style={{ borderColor: "rgba(52,211,153,.4)", color: "#34d399" }}
                >
                  {selectedNode.dossier_id ? "Dossier créé" : "✓ Fusionner en dossier"}
                </button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}
