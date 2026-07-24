"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Beaker,
  Rocket,
  TrendingUp,
  RefreshCw,
  Send,
  CheckCircle2,
  XCircle,
  HelpCircle,
  Loader2,
  Target,
  Trash2,
  FolderPlus,
  ChevronDown,
  X,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  fetchRndIdeas,
  fetchRndVision,
  injectRndIdea,
  archiveRndIdea,
  triggerRndCycle,
  type RndIdea,
} from "@/lib/rnd";
import { RndIdeaDetailModal } from "@/components/rnd/rnd-idea-detail-modal";
import { RndSubmitDossierModal } from "@/components/rnd/rnd-submit-dossier-modal";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function VerdictBadge({ verdict }: { verdict?: string | null }) {
  if (!verdict) return <span className="rounded-full bg-white/5 px-2 py-0.5 text-[10px] text-titanium/50">En attente</span>;
  const map: Record<string, { label: string; icon: React.ReactNode; cls: string }> = {
    GO: { label: "GO", icon: <CheckCircle2 className="h-3 w-3" />, cls: "bg-emerald-500/15 text-emerald-400 border-emerald-500/20" },
    MAYBE: { label: "MAYBE", icon: <HelpCircle className="h-3 w-3" />, cls: "bg-amber-500/15 text-amber-400 border-amber-500/20" },
    NO: { label: "NO", icon: <XCircle className="h-3 w-3" />, cls: "bg-red-500/15 text-red-400 border-red-500/20" },
  };
  const cfg = map[verdict] ?? map["MAYBE"];
  return (
    <span className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-[10px] font-semibold ${cfg.cls}`}>
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

// ---------------------------------------------------------------------------
// Idea card
// ---------------------------------------------------------------------------

function IdeaCard({
  idea,
  onOpen,
  onDelete,
  deleting,
}: {
  idea: RndIdea;
  onOpen: (idea: RndIdea) => void;
  onDelete: (idea: RndIdea) => void;
  deleting?: boolean;
}) {
  const reasoning = idea.reasoning ?? idea.verdict_reason;
  const preview =
    idea.description && idea.description !== idea.title
      ? idea.description
      : reasoning;

  return (
    <div className="group relative w-full rounded-xl border border-copper/10 bg-white/[0.02] p-4 transition hover:border-copper/25 hover:bg-white/[0.04]">
      <button
        type="button"
        className="w-full text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-copper/40 rounded-lg"
        onClick={() => onOpen(idea)}
      >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <div className="mb-1.5 flex flex-wrap items-center gap-2">
            <VerdictBadge verdict={idea.verdict} />
            {idea.domain && (
              <span className="rounded-full border border-white/10 px-2 py-0.5 text-[10px] text-titanium/60">
                {idea.domain}
              </span>
            )}
            {idea.dossier_id ? (
              <span className="rounded-full border border-emerald-500/25 bg-emerald-500/10 px-2 py-0.5 text-[10px] text-emerald-400">
                Dossier
              </span>
            ) : null}
            {idea.source && idea.source !== "rnd_agent" && (
              <span className="rounded-full border border-copper/20 bg-copper/5 px-2 py-0.5 text-[10px] text-copper/70">
                {idea.source}
              </span>
            )}
          </div>
          <p className="text-sm font-medium text-ivory/90 group-hover:text-ivory">
            {idea.title}
          </p>
          {preview ? (
            <p className="mt-1.5 line-clamp-3 text-xs leading-relaxed text-titanium/70">
              {preview}
            </p>
          ) : null}
          {idea.score != null && (
            <p className="mt-1 text-[11px] text-titanium/50">
              Score total : {idea.score}/30 · Cliquer pour le pitch
            </p>
          )}
        </div>
        {idea.score != null && (
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-copper/10 text-sm font-bold text-copper">
            {idea.score}
          </div>
        )}
      </div>
      </button>
      <Button
        type="button"
        size="icon"
        variant="ghost"
        disabled={deleting}
        aria-label="Archiver la proposition"
        className="absolute right-3 top-3 z-10 h-8 w-8 text-titanium/55 opacity-100 transition hover:bg-red-500/10 hover:text-red-400 sm:opacity-70 sm:group-hover:opacity-100"
        onClick={(e) => {
          e.stopPropagation();
          onDelete(idea);
        }}
      >
        {deleting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
      </Button>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

type FilterVerdict = "ALL" | "GO" | "MAYBE" | "NO";

interface RndCenterViewProps {
  onDossierCreated?: (dossierId: string) => void;
}

export function RndCenterView({ onDossierCreated }: RndCenterViewProps) {
  const [ideas, setIdeas] = useState<RndIdea[]>([]);
  const [vision, setVision] = useState("");
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<FilterVerdict>("ALL");
  const [cycleRunning, setCycleRunning] = useState(false);
  const [injectText, setInjectText] = useState("");
  const [injecting, setInjecting] = useState(false);
  const [selectedIdea, setSelectedIdea] = useState<RndIdea | null>(null);
  const [detailOpen, setDetailOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [submitModalOpen, setSubmitModalOpen] = useState(false);
  const [visionOpen, setVisionOpen] = useState(true);

  useEffect(() => {
    setVisionOpen(sessionStorage.getItem("rnd_vision_collapsed") !== "1");
  }, []);

  function toggleVision() {
    setVisionOpen((prev) => {
      const next = !prev;
      sessionStorage.setItem("rnd_vision_collapsed", next ? "0" : "1");
      return next;
    });
  }

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [ideasData, visionData] = await Promise.all([
        fetchRndIdeas(),
        fetchRndVision(),
      ]);
      setIdeas(ideasData);
      setVision(visionData);
    } catch {
      // API down — show empty state
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  const filtered = filter === "ALL" ? ideas : ideas.filter((i) => i.verdict === filter);

  async function handleCycle() {
    setCycleRunning(true);
    try {
      const msg = await triggerRndCycle();
      toast.success(msg);
      setTimeout(load, 5000);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    } finally {
      setCycleRunning(false);
    }
  }

  async function handleInject() {
    if (!injectText.trim()) return;
    setInjecting(true);
    try {
      await injectRndIdea(injectText.trim());
      toast.success("Idée enregistrée dans Propositions.");
      setInjectText("");
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    } finally {
      setInjecting(false);
    }
  }

  async function handleDelete(idea: RndIdea) {
    if (!window.confirm(`Archiver « ${idea.title} » ?`)) return;
    setDeletingId(idea.id);
    try {
      await archiveRndIdea(idea.id);
      toast.success("Proposition archivée.");
      if (selectedIdea?.id === idea.id) {
        setDetailOpen(false);
        setSelectedIdea(null);
      }
      await load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur");
    } finally {
      setDeletingId(null);
    }
  }

  const counts = {
    GO: ideas.filter((i) => i.verdict === "GO").length,
    MAYBE: ideas.filter((i) => i.verdict === "MAYBE").length,
    NO: ideas.filter((i) => i.verdict === "NO").length,
    pending: ideas.filter((i) => !i.verdict).length,
  };

  function openIdeaDetail(idea: RndIdea) {
    setSelectedIdea(idea);
    setDetailOpen(true);
  }

  if (loading) {
    return (
      <div className="flex min-h-[200px] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-copper/50" />
      </div>
    );
  }

  const isEmpty = ideas.length === 0;

  return (
    <div className="flex flex-col gap-4">
      {/* Header stats */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {[
          { label: "GO", value: counts.GO, icon: <Rocket className="h-4 w-4 text-emerald-400" />, cls: "border-emerald-500/20 bg-emerald-500/5" },
          { label: "Maybe", value: counts.MAYBE, icon: <HelpCircle className="h-4 w-4 text-amber-400" />, cls: "border-amber-500/20 bg-amber-500/5" },
          { label: "No", value: counts.NO, icon: <XCircle className="h-4 w-4 text-red-400" />, cls: "border-red-500/20 bg-red-500/5" },
          { label: "En attente", value: counts.pending, icon: <Beaker className="h-4 w-4 text-titanium/50" />, cls: "border-white/10 bg-white/[0.02]" },
        ].map(({ label, value, icon, cls }) => (
          <div key={label} className={`rounded-xl border p-3 ${cls}`}>
            <div className="flex items-center gap-2">
              {icon}
              <span className="text-xs text-titanium/70">{label}</span>
            </div>
            <p className="mt-1 text-2xl font-semibold text-ivory/90">{value}</p>
          </div>
        ))}
      </div>

      {/* Vision — repliable pour laisser plus de place à la liste sur petit écran */}
      {vision && visionOpen ? (
        <div className="flex shrink-0 items-start gap-2 rounded-xl border border-copper/15 bg-copper/[0.04] px-4 py-2.5">
          <Target className="mt-0.5 h-4 w-4 shrink-0 text-copper/70" />
          <p className="min-w-0 flex-1 text-xs leading-relaxed text-titanium/80">
            <span className="mr-1 font-semibold text-copper/90">Fil conducteur :</span>
            {vision.length > 200 ? vision.slice(0, 200) + "…" : vision}
          </p>
          <button
            type="button"
            onClick={toggleVision}
            aria-label="Replier le fil conducteur"
            title="Replier"
            className="shrink-0 rounded p-1 text-titanium/50 transition hover:bg-white/5 hover:text-ivory/80"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      ) : vision ? (
        <button
          type="button"
          onClick={toggleVision}
          className="flex shrink-0 items-center gap-1.5 self-start rounded-lg px-2 py-1 text-[11px] text-titanium/45 transition hover:text-copper/80"
        >
          <ChevronDown className="h-3 w-3" />
          Fil conducteur
        </button>
      ) : null}

      {/* Controls */}
      <div className="flex shrink-0 flex-wrap items-center gap-2">
        <div className="flex rounded-lg border border-white/10 p-0.5">
          {(["ALL", "GO", "MAYBE", "NO"] as FilterVerdict[]).map((v) => (
            <button
              key={v}
              onClick={() => setFilter(v)}
              className={`rounded-md px-3 py-1 text-xs font-medium transition ${
                filter === v
                  ? "bg-copper text-obsidian"
                  : "text-titanium/70 hover:text-ivory/80"
              }`}
            >
              {v}
            </button>
          ))}
        </div>
        <div className="ml-auto flex gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={load}
            className="border-white/10 text-titanium/70 hover:text-ivory/80"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleCycle}
            disabled={cycleRunning}
            className="border-copper/25 text-copper hover:bg-copper/10"
          >
            {cycleRunning ? (
              <><Loader2 className="mr-1.5 h-3.5 w-3.5 animate-spin" />Cycle en cours…</>
            ) : (
              <><TrendingUp className="mr-1.5 h-3.5 w-3.5" />Lancer un cycle R&D</>
            )}
          </Button>
        </div>
      </div>

      {/* Inject idea / submit dossier */}
      <div className="flex shrink-0 flex-col gap-2 sm:flex-row">
        <div className="flex min-w-0 flex-1 gap-2">
          <Textarea
            value={injectText}
            onChange={(e) => setInjectText(e.target.value)}
            placeholder="Idée rapide (1 ligne) — ou ouvre le formulaire dossier complet ↓"
            rows={2}
            className="min-h-[52px] resize-none border-copper/15 bg-white/[0.02] text-ivory/90 placeholder:text-titanium/50"
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                handleInject();
              }
            }}
          />
          <Button
            onClick={handleInject}
            disabled={injecting || !injectText.trim()}
            className="h-auto shrink-0 bg-copper px-4 hover:bg-copper"
            title="Idée rapide"
          >
            {injecting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Send className="h-4 w-4" />}
          </Button>
        </div>
        <Button
          type="button"
          variant="outline"
          onClick={() => setSubmitModalOpen(true)}
          className="h-auto shrink-0 border-copper/30 text-copper hover:bg-copper/10 sm:px-5"
        >
          <FolderPlus className="mr-2 h-4 w-4" />
          Soumettre un dossier
        </Button>
      </div>

      {/* Ideas list — flows with the page; the whole page scrolls to reveal
          more, instead of being boxed into a small internally-scrolled pane. */}
      <div>
        {isEmpty ? (
          <div className="flex min-h-[240px] flex-col items-center justify-center gap-4 text-center">
            <Beaker className="h-12 w-12 text-copper/20" />
            <div>
              <p className="text-sm font-medium text-ivory/60">Aucune idée R&D pour l&apos;instant</p>
              <p className="mt-1 text-xs text-titanium/40">Lance un cycle R&D pour générer les premières idées automatiquement.</p>
            </div>
            <Button
              size="sm"
              onClick={handleCycle}
              disabled={cycleRunning}
              className="bg-copper text-obsidian hover:bg-copper/90"
            >
              {cycleRunning ? (
                <><Loader2 className="mr-2 h-3.5 w-3.5 animate-spin" />En cours…</>
              ) : (
                <><Rocket className="mr-2 h-3.5 w-3.5" />Premier cycle R&D</>
              )}
            </Button>
          </div>
        ) : filtered.length === 0 ? (
          <div className="flex h-32 items-center justify-center text-sm text-titanium/40">
            Aucune idée avec ce filtre.
          </div>
        ) : (
          <div className="space-y-2 pb-4 pr-1">
            {filtered.map((idea) => (
              <IdeaCard
                key={idea.id}
                idea={idea}
                onOpen={openIdeaDetail}
                onDelete={handleDelete}
                deleting={deletingId === idea.id}
              />
            ))}
          </div>
        )}
      </div>

      <RndIdeaDetailModal
        idea={selectedIdea}
        open={detailOpen}
        onOpenChange={setDetailOpen}
        onRefresh={load}
        onPromoted={onDossierCreated}
        onArchive={async (archivedIdea) => {
          await handleDelete(archivedIdea);
        }}
      />

      <RndSubmitDossierModal
        open={submitModalOpen}
        onOpenChange={setSubmitModalOpen}
        onSubmitted={(dossierId) => {
          void load();
          onDossierCreated?.(dossierId);
        }}
      />
    </div>
  );
}
