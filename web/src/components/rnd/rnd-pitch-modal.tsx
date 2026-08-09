"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Globe,
  Crown,
  BarChart3,
  CheckCircle2,
  Circle,
  FolderPlus,
  HelpCircle,
  Lightbulb,
  Loader2,
  Megaphone,
  Route,
  Rocket,
  Sparkles,
  Target,
  Trash2,
  Users,
  XCircle,
  Zap,
} from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogTitle,
} from "@/components/ui/dialog";
import { MarkdownContent } from "@/components/shared/markdown-content";
import { RndCommitteePanel } from "@/components/rnd/rnd-committee-panel";
import { RndDeckPanel } from "@/components/rnd/rnd-deck-panel";
import { RndSocialPanel } from "@/components/rnd/rnd-social-panel";
import { RndCeoPanel } from "@/components/rnd/rnd-ceo-panel";
import { RndProductPanel } from "@/components/rnd/rnd-product-panel";
import { RndPipelinePanel } from "@/components/rnd/rnd-pipeline-panel";
import { RndVisualPanel } from "@/components/rnd/rnd-visual-panel";
import { RndFinancePanel } from "@/components/rnd/rnd-finance-panel";
import {
  fetchRndDossier,
  promoteRndIdea,
  type RndDossierDetail,
  type RndDossierSection,
} from "@/lib/rnd-dossier";
import type { RndIdea } from "@/lib/rnd";
import { fetchRndIdea } from "@/lib/rnd";
import { cn } from "@/lib/utils";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function VerdictBadge({ verdict }: { verdict?: string | null }) {
  if (!verdict) return null;
  const map: Record<string, { label: string; icon: React.ReactNode; cls: string }> = {
    GO: {
      label: "GO",
      icon: <CheckCircle2 className="h-3.5 w-3.5" />,
      cls: "bg-emerald-500/15 text-emerald-400 border-emerald-500/25",
    },
    MAYBE: {
      label: "MAYBE",
      icon: <HelpCircle className="h-3.5 w-3.5" />,
      cls: "bg-amber-500/15 text-amber-400 border-amber-500/25",
    },
    NO: {
      label: "NO",
      icon: <XCircle className="h-3.5 w-3.5" />,
      cls: "bg-red-500/15 text-red-400 border-red-500/25",
    },
  };
  const cfg = map[verdict] ?? map.MAYBE;
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold",
        cfg.cls
      )}
    >
      {cfg.icon}
      {cfg.label}
    </span>
  );
}

function ScorePill({ label, value, max = 10 }: { label: string; value?: number; max?: number }) {
  if (value == null) return null;
  return (
    <div className="rounded-lg border border-copper/10 bg-obsidian-deep/50 px-3 py-2">
      <p className="text-[10px] uppercase tracking-wider text-titanium/50">{label}</p>
      <p className="text-lg font-semibold text-copper">
        {value}
        <span className="text-sm font-normal text-titanium/50">/{max}</span>
      </p>
    </div>
  );
}

function isPlaceholder(md: string): boolean {
  const t = md.trim();
  return (
    !t ||
    t.startsWith("_À compléter") ||
    t.startsWith("_Business case à générer") ||
    t.length < 20
  );
}

function firstParagraph(md: string): string {
  return md.split(/\n\n+/)[0]?.replace(/^#+\s*/, "").trim() || md.trim();
}

function sectionContent(
  dossier: RndDossierDetail | null,
  key: string,
  fallback?: string
): string | null {
  const sec = dossier?.sections.find((s) => s.section_key === key);
  if (sec && !isPlaceholder(sec.content_md)) return sec.content_md;
  if (fallback?.trim()) return fallback;
  return null;
}

interface PitchBlock {
  id: string;
  group: string;
  title: string;
  subtitle?: string;
  content: string | null;
  section?: RndDossierSection;
}

function buildPitchBlocks(idea: RndIdea, dossier: RndDossierDetail | null): PitchBlock[] {
  const reasoning = idea.reasoning ?? idea.verdict_reason ?? null;

  const blocks: PitchBlock[] = [
    {
      id: "pitch",
      group: "Pitch",
      title: "En une phrase",
      subtitle: "L'essentiel du projet",
      content:
        sectionContent(dossier, "solution") ??
        (dossier?.tagline && dossier.tagline !== idea.title ? dossier.tagline : null) ??
        (idea.description !== idea.title ? idea.description : null) ??
        reasoning,
    },
    {
      id: "why_now",
      group: "Pourquoi",
      title: "Pourquoi maintenant",
      subtitle: "Timing & opportunité",
      content: idea.why_now ?? sectionContent(dossier, "market"),
    },
    {
      id: "problem",
      group: "Pourquoi",
      title: "Le problème",
      subtitle: "Douleur utilisateur / marché",
      content: sectionContent(dossier, "problem", idea.description),
    },
    {
      id: "solution",
      group: "Comment",
      title: "La solution",
      subtitle: "Proposition de valeur",
      content: sectionContent(dossier, "solution"),
    },
    {
      id: "mvp",
      group: "Comment",
      title: "MVP & périmètre",
      subtitle: "Ce qu'on livre en v1",
      content: sectionContent(dossier, "mvp", idea.next_step ?? undefined),
    },
    {
      id: "feasibility",
      group: "Comment",
      title: "Faisabilité",
      subtitle: "Technique & opérationnel",
      content: sectionContent(dossier, "feasibility"),
    },
    {
      id: "market",
      group: "Projet",
      title: "Marché & concurrence",
      subtitle: "Cible, taille, alternatives",
      content: sectionContent(dossier, "market"),
    },
    {
      id: "business_case",
      group: "Projet",
      title: "Business case",
      subtitle: "Coûts, revenus, viabilité",
      content: sectionContent(dossier, "business_case"),
    },
    {
      id: "risks",
      group: "Projet",
      title: "Risques",
      subtitle: "Ce qui peut bloquer",
      content: sectionContent(dossier, "risks"),
    },
    {
      id: "decision",
      group: "Projet",
      title: "Décision recommandée",
      subtitle: "Verdict agents + prochaine étape",
      content:
        sectionContent(dossier, "decision") ??
        (reasoning
          ? `${reasoning}\n\n**Prochaine étape :** ${idea.next_step ?? "À définir en comité."}`
          : idea.next_step ?? null),
    },
  ];

  const extraKeys = [
    "manufacturing",
    "lore",
    "visual_identity",
    "social_strategy",
  ] as const;

  for (const key of extraKeys) {
    const sec = dossier?.sections.find((s) => s.section_key === key);
    if (sec && !isPlaceholder(sec.content_md)) {
      blocks.push({
        id: key,
        group: "Spécifique",
        title: sec.title,
        content: sec.content_md,
        section: sec,
      });
    }
  }

  return blocks.filter((b) => b.content);
}

// ---------------------------------------------------------------------------
// Modal
// ---------------------------------------------------------------------------

export type PitchViewMode =
  | "pitch"
  | "committee"
  | "deck"
  | "visuals"
  | "social"
  | "ceo"
  | "product"
  | "pipeline";

export interface RndPitchModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  idea?: RndIdea | null;
  dossierId?: string | null;
  initialViewMode?: string;
  onPromoted?: (dossierId: string) => void;
  onRefresh?: () => void;
  onArchive?: (idea: RndIdea) => void | Promise<void>;
}

function parseInitialViewMode(value?: string): PitchViewMode {
  const allowed: PitchViewMode[] = [
    "pitch",
    "committee",
    "deck",
    "visuals",
    "social",
    "ceo",
    "product",
    "pipeline",
  ];
  return allowed.includes(value as PitchViewMode) ? (value as PitchViewMode) : "pitch";
}

export function RndPitchModal({
  open,
  onOpenChange,
  idea: ideaProp,
  dossierId: dossierIdProp,
  initialViewMode,
  onPromoted,
  onRefresh,
  onArchive,
}: RndPitchModalProps) {
  const [dossier, setDossier] = useState<RndDossierDetail | null>(null);
  const [ideaFromApi, setIdeaFromApi] = useState<RndIdea | null>(null);
  const [loading, setLoading] = useState(false);
  const [promoting, setPromoting] = useState(false);
  const [archiving, setArchiving] = useState(false);
  const [activeBlock, setActiveBlock] = useState("pitch");
  const [viewMode, setViewMode] = useState<PitchViewMode>("pitch");

  const resolvedDossierId = dossierIdProp ?? ideaProp?.dossier_id ?? null;

  const loadDossier = useCallback(async (id: string, silent = false) => {
    if (!silent) setLoading(true);
    try {
      setDossier(await fetchRndDossier(id));
    } catch (e) {
      if (!silent) {
        setDossier(null);
        toast.error(e instanceof Error ? e.message : "Dossier introuvable");
      }
    } finally {
      if (!silent) setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (!open) {
      setDossier(null);
      setIdeaFromApi(null);
      setActiveBlock("pitch");
      setViewMode("pitch");
      return;
    }
    setViewMode(parseInitialViewMode(initialViewMode));
    if (resolvedDossierId) {
      void loadDossier(resolvedDossierId);
    } else {
      setDossier(null);
      setLoading(false);
    }
  }, [open, resolvedDossierId, initialViewMode, loadDossier]);

  useEffect(() => {
    if (!open || ideaProp || !dossier?.idea_legacy_id) return;
    void fetchRndIdea(dossier.idea_legacy_id)
      .then(setIdeaFromApi)
      .catch(() => setIdeaFromApi(null));
  }, [open, ideaProp, dossier?.idea_legacy_id]);

  useEffect(() => {
    if (!open || !dossier?.id || dossier.finance_json) return;
    const id = dossier.id;
    const timer = window.setInterval(() => void loadDossier(id, true), 5000);
    const stop = window.setTimeout(() => window.clearInterval(timer), 120_000);
    return () => {
      window.clearInterval(timer);
      window.clearTimeout(stop);
    };
  }, [open, dossier?.id, dossier?.finance_json, loadDossier]);

  const idea: RndIdea | null = useMemo(
    () =>
      ideaProp ??
      ideaFromApi ??
      (dossier
        ? {
            id: dossier.idea_legacy_id ?? dossier.idea_id,
            title: dossier.title,
            description: dossier.tagline ?? dossier.title,
            domain: dossier.domain,
            dossier_id: dossier.id,
          }
        : null),
    [ideaProp, ideaFromApi, dossier],
  );

  const blocks = useMemo(
    () => (idea ? buildPitchBlocks(idea, dossier) : []),
    [idea, dossier]
  );

  const groups = useMemo(() => {
    const order = ["Pitch", "Pourquoi", "Comment", "Projet", "Spécifique"];
    const seen = new Set<string>();
    const g: string[] = [];
    for (const b of blocks) {
      if (!seen.has(b.group)) {
        seen.add(b.group);
        g.push(b.group);
      }
    }
    return order.filter((x) => g.includes(x));
  }, [blocks]);

  async function handlePromote() {
    if (!idea) return;
    setPromoting(true);
    try {
      const result = await promoteRndIdea(idea.id);
      toast.success(result.message);
      if (result.enriching) {
        toast.info("Enrichissement en cours (30–60 s)…", { duration: 8000 });
      }
      setDossier(result.dossier);
      onRefresh?.();
      onPromoted?.(result.dossier.id);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Erreur création dossier");
    } finally {
      setPromoting(false);
    }
  }

  async function handleArchive() {
    if (!idea || !onArchive) return;
    setArchiving(true);
    try {
      await onArchive(idea);
    } finally {
      setArchiving(false);
    }
  }

  if (!open) return null;

  if (!idea && loading) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="flex h-48 flex-col items-center justify-center gap-3 border-copper/25 bg-obsidian-2">
          <Loader2 className="h-8 w-8 animate-spin text-copper/50" />
          <p className="text-xs text-titanium/60">Chargement du dossier… (peut prendre quelques secondes)</p>
        </DialogContent>
      </Dialog>
    );
  }

  if (!idea) return null;

  const elevator = blocks.find((b) => b.id === "pitch")?.content;
  const reasoning = idea.reasoning ?? idea.verdict_reason;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        showCloseButton
        className={cn(
          "flex h-[calc(100dvh-1.25rem)] w-[calc(100vw-1.25rem)] max-w-none flex-col gap-0 overflow-hidden",
          "rounded-2xl border-copper/25 bg-obsidian-2 p-0 text-ivory shadow-2xl sm:max-w-none"
        )}
      >
        <DialogTitle className="sr-only">{idea.title} — pitch R&D</DialogTitle>

        {/* Hero */}
        <header className="shrink-0 border-b border-copper/15 bg-gradient-to-r from-copper/[0.08] via-transparent to-transparent px-6 py-6 sm:px-8">
          <div className="mx-auto flex max-w-7xl flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="min-w-0 flex-1">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <VerdictBadge verdict={idea.verdict} />
                {idea.domain ? (
                  <span className="rounded-full border border-copper/15 px-2.5 py-1 text-xs text-titanium/70">
                    {idea.domain}
                  </span>
                ) : null}
                {idea.effort ? (
                  <span className="rounded-full border border-copper/15 px-2.5 py-1 text-xs text-titanium/70">
                    Effort {idea.effort}
                  </span>
                ) : null}
                {dossier ? (
                  <span className="rounded-full border border-emerald-500/25 bg-emerald-500/10 px-2.5 py-1 text-xs text-emerald-400">
                    Dossier R&D
                  </span>
                ) : null}
                {dossier?.status === "committee_active" ? (
                  <span className="inline-flex items-center gap-1 rounded-full border border-copper/30 bg-copper/15 px-2.5 py-1 text-xs text-copper">
                    <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-copper" />
                    Comité actif
                  </span>
                ) : null}
              </div>
              <h1 className="font-title text-3xl font-medium leading-tight text-ivory sm:text-4xl">
                {idea.title}
              </h1>
              {elevator ? (
                <p className="mt-3 max-w-3xl text-base leading-relaxed text-ivory/85 sm:text-lg">
                  {firstParagraph(elevator)}
                </p>
              ) : null}
            </div>
            <div className="flex shrink-0 flex-wrap items-end gap-2">
              {dossier ? (
                <Button
                  type="button"
                  onClick={() => setViewMode((m) => (m === "committee" ? "pitch" : "committee"))}
                  className={cn(
                    "mb-0.5",
                    viewMode === "committee"
                      ? "bg-copper text-obsidian hover:bg-copper/90"
                      : "border-copper/40 bg-copper/10 text-copper hover:bg-copper/20"
                  )}
                  variant={viewMode === "committee" ? "default" : "outline"}
                >
                  <Users className="mr-2 h-4 w-4" />
                  {viewMode === "committee" ? "Retour au pitch" : "Salle de réunion"}
                </Button>
              ) : null}
              {idea.score != null ? (
                <div className="rounded-xl border border-copper/20 bg-copper/10 px-4 py-3 text-center">
                  <p className="text-[10px] uppercase tracking-wider text-copper/70">Score R&D</p>
                  <p className="text-2xl font-bold text-copper-glow">
                    {idea.score}
                    <span className="text-sm text-titanium/50">/30</span>
                  </p>
                </div>
              ) : null}
              <ScorePill label="Marché" value={idea.market_score} />
              <ScorePill label="Faisabilité" value={idea.feasibility_score} />
              <ScorePill label="Vision" value={idea.vision_score} />
            </div>
          </div>
        </header>

        {/* Body */}
        <div className="flex min-h-0 flex-1">
          {viewMode === "committee" && dossier ? (
            <div className="flex min-h-0 w-full flex-col p-4 sm:p-6">
              <RndCommitteePanel
                dossierId={dossier.id}
                dossierTitle={dossier.title}
                onClosed={() => void loadDossier(dossier.id, true)}
              />
            </div>
          ) : viewMode === "deck" && dossier ? (
            <div className="flex min-h-0 w-full flex-col overflow-y-auto p-4 sm:p-6">
              <RndDeckPanel
                dossierId={dossier.id}
                dossierTitle={dossier.title}
                deckHtmlPath={dossier.deck_html_path}
                deckPdfPath={dossier.deck_pdf_path}
                onGenerated={() => void loadDossier(dossier.id, true)}
              />
            </div>
          ) : viewMode === "visuals" && dossier ? (
            <div className="flex min-h-0 w-full flex-col overflow-y-auto p-4 sm:p-6">
              <RndVisualPanel
                dossierId={dossier.id}
                dossierTitle={dossier.title}
                onGenerated={() => void loadDossier(dossier.id, true)}
              />
            </div>
          ) : viewMode === "social" && dossier ? (
            <div className="flex min-h-0 w-full flex-col overflow-y-auto p-4 sm:p-6">
              <RndSocialPanel
                dossierId={dossier.id}
                dossierTitle={dossier.title}
                dossierStatus={dossier.status}
                ceoStatus={dossier.ceo_status}
                onUpdated={() => void loadDossier(dossier.id, true)}
              />
            </div>
          ) : viewMode === "pipeline" && dossier ? (
            <div className="flex min-h-0 w-full flex-col overflow-y-auto p-4 sm:p-6">
              <RndPipelinePanel
                dossierId={dossier.id}
                onNavigateTab={(tab) =>
                  setViewMode(
                    tab as typeof viewMode
                  )
                }
              />
            </div>
          ) : viewMode === "product" && dossier ? (
            <div className="flex min-h-0 w-full flex-col overflow-y-auto p-4 sm:p-6">
              <RndProductPanel
                dossierId={dossier.id}
                dossierTitle={dossier.title}
                dossierStatus={dossier.status}
                ceoStatus={dossier.ceo_status}
                onUpdated={() => void loadDossier(dossier.id, true)}
              />
            </div>
          ) : viewMode === "ceo" && dossier ? (
            <div className="flex min-h-0 w-full flex-col overflow-y-auto p-4 sm:p-6">
              <RndCeoPanel
                dossierId={dossier.id}
                dossierTitle={dossier.title}
                dossierStatus={dossier.status}
                onUpdated={() => void loadDossier(dossier.id, true)}
              />
            </div>
          ) : (
          <>
          {/* Nav */}
          <nav className="hidden w-52 shrink-0 flex-col gap-4 overflow-y-auto border-r border-copper/10 bg-obsidian/40 px-3 py-4 lg:flex">
            {groups.map((group) => (
              <div key={group}>
                <p className="label-caps mb-1.5 px-2 text-titanium/45">{group}</p>
                <ul className="space-y-0.5">
                  {blocks
                    .filter((b) => b.group === group)
                    .map((b) => (
                      <li key={b.id}>
                        <button
                          type="button"
                          onClick={() => {
                            setActiveBlock(b.id);
                            document.getElementById(`pitch-block-${b.id}`)?.scrollIntoView({
                              behavior: "smooth",
                              block: "start",
                            });
                          }}
                          className={cn(
                            "w-full rounded-lg px-2 py-1.5 text-left text-xs transition",
                            activeBlock === b.id
                              ? "bg-copper/15 text-copper"
                              : "text-titanium/70 hover:bg-obsidian-deep/50 hover:text-ivory"
                          )}
                        >
                          {b.title}
                        </button>
                      </li>
                    ))}
                </ul>
              </div>
            ))}
          </nav>

          {/* Content */}
          <div className="min-h-0 flex-1 overflow-y-auto px-4 py-5 sm:px-8">
            <div className="mx-auto max-w-4xl space-y-8 pb-8">
              {loading && !dossier ? (
                <div className="flex h-48 items-center justify-center">
                  <Loader2 className="h-8 w-8 animate-spin text-copper/50" />
                </div>
              ) : blocks.length === 0 ? (
                <div className="rounded-xl border border-copper/15 bg-obsidian-deep/40 p-8 text-center">
                  <Lightbulb className="mx-auto mb-3 h-10 w-10 text-copper/30" />
                  <p className="text-sm text-titanium/70">
                    Crée le dossier R&D pour générer le pitch complet (pourquoi, comment, business case…).
                  </p>
                </div>
              ) : (
                blocks.map((block) => (
                  <article
                    key={block.id}
                    id={`pitch-block-${block.id}`}
                    className="scroll-mt-4 rounded-2xl border border-copper/12 bg-obsidian-deep/40 p-6 sm:p-8"
                  >
                    <div className="mb-4 flex items-start gap-3">
                      {block.group === "Pourquoi" ? (
                        <Zap className="mt-0.5 h-5 w-5 shrink-0 text-amber-400/80" />
                      ) : block.group === "Comment" ? (
                        <Rocket className="mt-0.5 h-5 w-5 shrink-0 text-copper/80" />
                      ) : block.group === "Projet" ? (
                        <BarChart3 className="mt-0.5 h-5 w-5 shrink-0 text-emerald-400/80" />
                      ) : (
                        <Target className="mt-0.5 h-5 w-5 shrink-0 text-copper/70" />
                      )}
                      <div>
                        <p className="text-[10px] font-semibold uppercase tracking-widest text-copper/60">
                          {block.group}
                        </p>
                        <h2 className="font-title text-xl text-ivory">{block.title}</h2>
                        {block.subtitle ? (
                          <p className="mt-0.5 text-sm text-titanium/55">{block.subtitle}</p>
                        ) : null}
                      </div>
                      {block.section ? (
                        <span className="ml-auto flex items-center gap-1 text-[10px] text-titanium/45">
                          {block.section.status === "validated" ? (
                            <CheckCircle2 className="h-3 w-3 text-emerald-400" />
                          ) : (
                            <Circle className="h-3 w-3" />
                          )}
                          {block.section.status}
                        </span>
                      ) : null}
                    </div>

                    {block.id === "business_case" && dossier?.finance_json ? (
                      <div className="space-y-4">
                        <RndFinancePanel finance={dossier.finance_json} />
                        {block.content && !isPlaceholder(block.content) ? (
                          <MarkdownContent className="prose prose-invert max-w-none prose-p:text-ivory/85 prose-headings:text-ivory prose-li:text-ivory/85">
                            {block.content}
                          </MarkdownContent>
                        ) : null}
                      </div>
                    ) : block.id === "pitch" ? (
                      <p className="text-lg font-medium leading-relaxed text-ivory/90">
                        {block.content}
                      </p>
                    ) : (
                      <MarkdownContent className="prose prose-invert max-w-none prose-p:text-ivory/85 prose-headings:text-ivory prose-li:text-ivory/85">
                        {block.content ?? ""}
                      </MarkdownContent>
                    )}
                  </article>
                ))
              )}

              {reasoning && !blocks.some((b) => b.id === "decision") ? (
                <article className="rounded-2xl border border-copper/12 bg-obsidian-deep/40 p-6">
                  <h2 className="font-title text-lg text-ivory">Analyse agents R&D</h2>
                  <p className="mt-3 whitespace-pre-wrap text-sm italic leading-relaxed text-titanium/85">
                    {reasoning}
                  </p>
                </article>
              ) : null}

              {!dossier?.finance_json && dossier ? (
                <p className="text-center text-xs text-amber-200/70">
                  Business case en cours de génération…
                </p>
              ) : null}
            </div>
          </div>
          </>
          )}
        </div>

        {/* Footer — hidden in committee/deck to avoid overlapping chat */}
        {viewMode === "pitch" ? (
        <footer className="flex shrink-0 flex-wrap items-center justify-between gap-3 border-t border-copper/15 bg-obsidian/60 px-6 py-4 sm:px-8">
          <p className="text-xs text-titanium/50">
            {dossier
              ? `${dossier.sections_validated_count}/${dossier.sections_total_count} sections validées · ${dossier.slug}`
              : "Pitch idée — crée un dossier pour enrichir avec les agents"}
          </p>
          <div className="flex flex-wrap gap-2">
            {dossier ? (
              <>
                <Button
                  type="button"
                  variant="outline"
                  className="border-copper/35 text-copper hover:bg-copper/10"
                  onClick={() => setViewMode("committee")}
                >
                  <Users className="mr-2 h-4 w-4" />
                  Salle de réunion
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="border-copper/15 text-titanium/80 hover:bg-obsidian-deep/50"
                  onClick={() => setViewMode("deck")}
                >
                  <BarChart3 className="mr-2 h-4 w-4" />
                  Deck pitch
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="border-copper/15 text-titanium/80 hover:bg-obsidian-deep/50"
                  onClick={() => setViewMode("visuals")}
                >
                  <Sparkles className="mr-2 h-4 w-4" />
                  Visuels
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="border-copper/15 text-titanium/80 hover:bg-obsidian-deep/50"
                  onClick={() => setViewMode("ceo")}
                >
                  <Crown className="mr-2 h-4 w-4" />
                  Dossier CEO
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="border-copper/35 text-copper hover:bg-copper/10"
                  onClick={() => setViewMode("pipeline")}
                >
                  <Route className="mr-2 h-4 w-4" />
                  Pipeline
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="border-copper/15 text-titanium/80 hover:bg-obsidian-deep/50"
                  onClick={() => setViewMode("product")}
                >
                  <Globe className="mr-2 h-4 w-4" />
                  Fiche produit
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  className="border-copper/15 text-titanium/80 hover:bg-obsidian-deep/50"
                  onClick={() => setViewMode("social")}
                >
                  <Megaphone className="mr-2 h-4 w-4" />
                  Social
                </Button>
              </>
            ) : null}
            {!resolvedDossierId && !dossier ? (
              <>
                {onArchive ? (
                  <Button
                    type="button"
                    variant="outline"
                    disabled={archiving || promoting}
                    className="border-red-500/30 text-red-400 hover:bg-red-500/10"
                    onClick={() => void handleArchive()}
                  >
                    {archiving ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Archivage…
                      </>
                    ) : (
                      <>
                        <Trash2 className="mr-2 h-4 w-4" />
                        Archiver la proposition
                      </>
                    )}
                  </Button>
                ) : null}
                <Button
                  onClick={handlePromote}
                  disabled={promoting || archiving}
                  className="bg-copper text-obsidian hover:bg-copper/90"
                >
                  {promoting ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Génération du dossier…
                    </>
                  ) : (
                    <>
                      <FolderPlus className="mr-2 h-4 w-4" />
                      Créer le dossier & pitch complet
                    </>
                  )}
                </Button>
              </>
            ) : null}
            <Button variant="outline" className="border-copper/15" onClick={() => onOpenChange(false)}>
              Fermer
            </Button>
          </div>
        </footer>
        ) : (
        <footer className="flex shrink-0 items-center justify-end gap-2 border-t border-copper/15 bg-obsidian/60 px-6 py-3 sm:px-8">
          <Button
            type="button"
            variant="outline"
            className="border-copper/15"
            onClick={() => setViewMode("pitch")}
          >
            Retour au pitch
          </Button>
          <Button variant="outline" className="border-copper/15" onClick={() => onOpenChange(false)}>
            Fermer
          </Button>
        </footer>
        )}
      </DialogContent>
    </Dialog>
  );
}
