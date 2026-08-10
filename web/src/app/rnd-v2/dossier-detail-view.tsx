"use client";

import { useCallback, useEffect, useState } from "react";
import { Archive, Loader2, X } from "lucide-react";
import { toast } from "sonner";
import { RndCeoPanel } from "@/components/rnd/rnd-ceo-panel";
import { RndCommitteePanel } from "@/components/rnd/rnd-committee-panel";
import { RndDeckPanel } from "@/components/rnd/rnd-deck-panel";
import { RndDossierSectionsPanel } from "@/components/rnd/rnd-dossier-sections-panel";
import { RndFinancePanel } from "@/components/rnd/rnd-finance-panel";
import { RndPipelinePanel } from "@/components/rnd/rnd-pipeline-panel";
import { RndProductPanel } from "@/components/rnd/rnd-product-panel";
import { RndSocialPanel } from "@/components/rnd/rnd-social-panel";
import { RndVisualPanel } from "@/components/rnd/rnd-visual-panel";
import {
  fetchDossierPipeline,
  fetchRndDossier,
  fetchRndDossierEvents,
  promoteRndIdea,
  type RndDossierDetail,
  type RndDossierEvent,
  type RndPipelineResponse,
} from "@/lib/rnd-dossier";
import { archiveRndIdea, updateIncubatorStage, type RndIdea } from "@/lib/rnd";
import { C } from "../app-v2/shared";

/* Vue détail complète du dossier (Phase 23, correctif Phase 27, ROADMAP.md)
   — overlay plein écran ouvert depuis Pipeline/Dossiers. La version Phase 23
   condensait le dossier en 9 onglets "pitch" narratifs
   (buildPitchBlocks-like) ; Emilie a jugé ça insuffisant ("le dossier doit
   être beaucoup plus complet") et choisi explicitement le vrai espace de
   travail (finance/comité/deck/social/CEO), pas juste les sections en
   entier. Ce correctif remplace donc le contenu par les vrais panneaux déjà
   existants et fonctionnels de l'ancien système (`web/src/components/rnd/
   rnd-*-panel.tsx`), réutilisés tels quels (aucune logique/API réécrite) —
   seuls l'en-tête/scrim/actions de cette vue sont conservés. Reskin visuel
   de ces panneaux (encore en shadcn/Tailwind sémantique, pas le système `C`
   inline) volontairement différé : périmètre fonctionnel d'abord, voir
   ROADMAP.md Phase 27 (correctif) pour la justification. */

const TABS = [
  { id: "sections", label: "Sections" },
  { id: "committee", label: "Comité" },
  { id: "deck", label: "Deck" },
  { id: "visuals", label: "Visuels" },
  { id: "social", label: "Social" },
  { id: "ceo", label: "Dossier CEO" },
  { id: "product", label: "Fiche produit" },
  { id: "pipeline", label: "Pipeline" },
] as const;
type TabId = (typeof TABS)[number]["id"];

/* Le pipeline backend (services/rnd_pipeline.py::STAGE_DEFS) ne connaît que
   6 valeurs de `tab` (pitch/committee/visuals/social/ceo/product) — `pitch`
   est l'équivalent historique de l'onglet "sections" d'aujourd'hui ; les 5
   autres passent 1:1. */
const PIPELINE_TAB_MAP: Record<string, TabId> = { pitch: "sections" };

const VERDICT_COLOR: Record<string, string> = {
  GO: "#2DD4BF",
  MAYBE: "#E0A95C",
  NO: "#f87171",
};

function PipelineStrip({
  pipeline,
  onNavigate,
}: {
  pipeline: RndPipelineResponse;
  onNavigate: (tab: string) => void;
}) {
  return (
    <div className="flex items-center gap-1.5 overflow-x-auto">
      {pipeline.stages.map((stage, i) => (
        <div key={stage.id} className="flex shrink-0 items-center gap-1.5">
          <span
            role={stage.status !== "locked" && stage.tab ? "button" : undefined}
            tabIndex={stage.status !== "locked" && stage.tab ? 0 : undefined}
            onClick={() => stage.status !== "locked" && stage.tab && onNavigate(stage.tab)}
            className="flex h-5 items-center rounded-full border px-2 text-[9px] whitespace-nowrap"
            style={{
              cursor: stage.status !== "locked" && stage.tab ? "pointer" : undefined,
              ...(stage.status === "done"
                ? { borderColor: "rgba(45,212,191,.35)", background: "rgba(45,212,191,.1)", color: "#5EEAD4" }
                : stage.status === "in_progress"
                  ? { borderColor: "rgba(224,155,106,.45)", background: "rgba(224,155,106,.12)", color: C.copperLight }
                  : { borderColor: C.lineSoft, color: C.faint }),
            }}
          >
            {stage.label}
          </span>
          {i < pipeline.stages.length - 1 ? (
            <span className="h-px w-3" style={{ background: C.lineSoft }} />
          ) : null}
        </div>
      ))}
    </div>
  );
}

export function DossierDetailView({
  idea,
  onClose,
  onIdeaUpdated,
  onIdeaArchived,
}: {
  idea: RndIdea | null;
  onClose: () => void;
  onIdeaUpdated?: (idea: RndIdea) => void;
  onIdeaArchived?: (ideaId: string) => void;
}) {
  const [dossier, setDossier] = useState<RndDossierDetail | null>(null);
  const [events, setEvents] = useState<RndDossierEvent[]>([]);
  const [pipeline, setPipeline] = useState<RndPipelineResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [promoting, setPromoting] = useState(false);
  const [incubating, setIncubating] = useState(false);
  const [archiving, setArchiving] = useState(false);
  const [activeId, setActiveId] = useState<TabId>("sections");
  const [activeSection, setActiveSection] = useState<string | null>(null);

  const load = useCallback(async (dossierId: string, opts?: { silent?: boolean }) => {
    if (!opts?.silent) setLoading(true);
    try {
      const [d, ev] = await Promise.all([fetchRndDossier(dossierId), fetchRndDossierEvents(dossierId)]);
      setDossier(d);
      setEvents(ev);
      setActiveSection((prev) => prev ?? d.sections[0]?.section_key ?? null);
      void fetchDossierPipeline(d.id)
        .then((p) => setPipeline(p))
        .catch(() => undefined);
    } catch {
      if (!opts?.silent) {
        setDossier(null);
        setEvents([]);
      }
    } finally {
      if (!opts?.silent) setLoading(false);
    }
  }, []);

  useEffect(() => {
    setDossier(null);
    setEvents([]);
    setPipeline(null);
    setActiveId("sections");
    setActiveSection(null);
    if (!idea?.dossier_id) return;
    void load(idea.dossier_id);
  }, [idea?.dossier_id, load]);

  // Poll pendant l'enrichissement en arrière-plan (finance_json pas encore
  // arrivé) — même pattern que rnd-dossier-workspace.tsx.
  useEffect(() => {
    if (!dossier?.id || dossier.finance_json) return;
    const id = dossier.id;
    const timer = window.setInterval(() => void load(id, { silent: true }), 5000);
    const stop = window.setTimeout(() => window.clearInterval(timer), 120_000);
    return () => {
      window.clearInterval(timer);
      window.clearTimeout(stop);
    };
  }, [dossier?.id, dossier?.finance_json, load]);

  if (!idea) return null;

  const verdictColor = idea.verdict ? VERDICT_COLOR[idea.verdict] : C.faint;

  function handleNavigateTab(tab: string) {
    setActiveId(PIPELINE_TAB_MAP[tab] ?? (tab as TabId));
  }

  async function handlePromote() {
    if (!idea) return;
    setPromoting(true);
    try {
      const res = await promoteRndIdea(idea.id);
      toast.success(`Dossier créé : ${res.dossier.title}`);
      onIdeaUpdated?.({ ...idea, dossier_id: res.dossier.id });
      void load(res.dossier.id);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Échec de la création du dossier");
    } finally {
      setPromoting(false);
    }
  }

  /** "Incuber" = entrer dans le Kanban Incubateur (Phase 24) à l'étape
   * Prototype — ne fait rien de plus ici (le vrai dispatch département se
   * fait depuis l'onglet Incubateur, pas depuis cette vue). */
  async function handleIncubate() {
    if (!idea) return;
    setIncubating(true);
    try {
      await updateIncubatorStage(idea.id, "prototype");
      toast.success(`« ${idea.title} » envoyée dans l'Incubateur (étape Prototype).`);
      onIdeaUpdated?.({ ...idea, incubator_stage: "prototype" });
      onClose();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Échec de l'envoi vers l'Incubateur");
    } finally {
      setIncubating(false);
    }
  }

  async function handleArchive() {
    if (!idea) return;
    if (!window.confirm(`Supprimer « ${idea.title} » ? Cette action est irréversible.`)) return;
    setArchiving(true);
    try {
      await archiveRndIdea(idea.id);
      toast.success(`« ${idea.title} » supprimée.`);
      onIdeaArchived?.(idea.id);
      onClose();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Échec de la suppression");
    } finally {
      setArchiving(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-8"
      style={{ background: "rgba(6,7,10,.82)" }}
      onClick={onClose}
    >
      <div
        className="flex h-full max-h-[92vh] w-full max-w-[1180px] flex-col overflow-hidden rounded-2xl border"
        style={{
          borderColor: C.lineStrong,
          background: "radial-gradient(1200px 500px at 50% -10%, rgba(224,155,106,.08), transparent 60%), #0B0C0E",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex shrink-0 flex-col gap-4 border-b px-6 py-5" style={{ borderColor: C.line }}>
          <div className="flex items-start justify-between gap-4">
            <div className="min-w-0">
              <p className="text-[9.5px] uppercase tracking-[1.5px]" style={{ color: C.faint }}>
                {idea.domain || "Idée R&D"}
              </p>
              <h2 className="mt-1 truncate text-[22px] font-bold" style={{ color: C.ivory }}>
                {idea.title}
              </h2>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border"
              style={{ borderColor: C.line, color: C.warm }}
              aria-label="Fermer"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <div className="relative h-14 w-14 shrink-0">
              <svg width="56" height="56" viewBox="0 0 56 56">
                <circle cx="28" cy="28" r="23" fill="none" stroke="rgba(224,155,106,.15)" strokeWidth="5" />
                {idea.score != null ? (
                  <circle
                    cx="28"
                    cy="28"
                    r="23"
                    fill="none"
                    stroke={C.copper}
                    strokeWidth="5"
                    strokeLinecap="round"
                    strokeDasharray={`${((idea.score / 100) * 2 * Math.PI * 23).toFixed(1)} ${(2 * Math.PI * 23).toFixed(1)}`}
                    transform="rotate(-90 28 28)"
                  />
                ) : null}
              </svg>
              <span className="absolute inset-0 flex items-center justify-center text-[13px] font-semibold" style={{ color: C.ivory }}>
                {idea.score ?? "—"}
              </span>
            </div>
            {idea.verdict ? (
              <span
                className="rounded-full border px-3 py-1 text-[11px] font-semibold"
                style={{ borderColor: `${verdictColor}55`, background: `${verdictColor}1F`, color: verdictColor }}
              >
                {idea.verdict}
              </span>
            ) : null}
            <div className="flex gap-3 text-[10px]" style={{ color: C.faint }}>
              <span>
                Marché <b style={{ color: C.warm }}>{idea.market_score ?? "—"}/10</b>
              </span>
              <span>
                Tech <b style={{ color: C.warm }}>{idea.feasibility_score ?? "—"}/10</b>
              </span>
              <span>
                Business <b style={{ color: C.warm }}>{idea.vision_score ?? "—"}/10</b>
              </span>
            </div>
          </div>

          {pipeline ? <PipelineStrip pipeline={pipeline} onNavigate={handleNavigateTab} /> : null}

          {/* 3 choix explicites (demande Emilie) : garder pour réfléchir
              (= fermer sans action), incuber (Kanban Incubateur, Phase 24),
              supprimer (archiveRndIdea, déjà existant mais jamais câblé sur
              aucune des deux vues détail R&D jusqu'ici). */}
          <div className="flex flex-wrap items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="rounded-full border px-3 py-1.5 text-[10.5px]"
              style={{ borderColor: C.lineSoft, color: C.warm }}
            >
              Garder pour réfléchir
            </button>
            {idea.incubator_stage !== "departement" ? (
              <button
                type="button"
                onClick={() => void handleIncubate()}
                disabled={incubating || archiving}
                className="flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[10.5px] disabled:opacity-40"
                style={{ borderColor: "rgba(224,155,106,.45)", background: "rgba(224,155,106,.1)", color: C.copperLight }}
              >
                {incubating ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
                🧪 Incuber
              </button>
            ) : null}
            <button
              type="button"
              onClick={() => void handleArchive()}
              disabled={incubating || archiving}
              className="flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[10.5px] disabled:opacity-40"
              style={{ borderColor: "rgba(248,113,113,.35)", color: "#f87171" }}
            >
              {archiving ? <Loader2 className="h-3 w-3 animate-spin" /> : <Archive className="h-3 w-3" />}
              Supprimer
            </button>
          </div>
        </div>

        {/* Contenu */}
        <div className="flex min-h-0 flex-1 flex-col">
          {loading ? (
            <div className="flex flex-1 items-center justify-center gap-2 py-16 text-[12px]" style={{ color: C.faint }}>
              <Loader2 className="h-4 w-4 animate-spin" />
              Chargement du dossier…
            </div>
          ) : !idea.dossier_id ? (
            <div className="flex flex-1 items-center justify-center px-6 py-16">
              <div className="flex max-w-md flex-col items-center gap-3 text-center">
                <p className="text-[12px]" style={{ color: C.dim }}>
                  Juste l&apos;évaluation initiale de l&apos;agent — pas encore de dossier détaillé
                  (sections, finance, comité, deck, social, CEO...).
                </p>
                <button
                  type="button"
                  onClick={() => void handlePromote()}
                  disabled={promoting}
                  className="flex shrink-0 items-center gap-1.5 rounded-full border px-4 py-1.5 text-[11px]"
                  style={{ borderColor: "rgba(224,155,106,.45)", background: "rgba(224,155,106,.1)", color: C.copperLight }}
                >
                  {promoting ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
                  Créer le dossier détaillé →
                </button>
              </div>
            </div>
          ) : !dossier ? (
            <div className="flex flex-1 items-center justify-center px-6 py-16 text-center">
              <p className="text-[12px]" style={{ color: C.dim }}>
                Dossier introuvable — réessaie ou ferme cette fenêtre.
              </p>
            </div>
          ) : (
            <>
              <div className="flex gap-4 overflow-x-auto border-b px-6 pt-3" style={{ borderColor: C.lineSoft }}>
                {TABS.map((t) => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setActiveId(t.id)}
                    className="shrink-0 whitespace-nowrap border-b-2 pb-2 text-[10.5px] tracking-[0.3px]"
                    style={{ borderColor: activeId === t.id ? C.copper : "transparent", color: activeId === t.id ? "#F5F2EA" : C.faint }}
                  >
                    {t.label.toUpperCase()}
                  </button>
                ))}
              </div>

              {activeId === "sections" ? (
                <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto px-6 py-5">
                  {dossier.finance_json ? (
                    <RndFinancePanel finance={dossier.finance_json} />
                  ) : (
                    <div
                      className="rounded-xl border px-4 py-2 text-[11px]"
                      style={{ borderColor: "rgba(224,169,92,.3)", background: "rgba(224,169,92,.08)", color: "#E0A95C" }}
                    >
                      Enrichissement en cours — business case et sections LLM arrivent sous ~1 min.
                    </div>
                  )}
                  <RndDossierSectionsPanel
                    dossier={dossier}
                    events={events}
                    activeSection={activeSection}
                    onSelectSection={setActiveSection}
                    onUpdated={() => void load(dossier.id, { silent: true })}
                  />
                </div>
              ) : activeId === "committee" ? (
                <div className="flex min-h-0 flex-1 flex-col p-4 sm:p-6">
                  <RndCommitteePanel
                    dossierId={dossier.id}
                    dossierTitle={dossier.title}
                    activeSection={activeSection}
                    onClosed={() => void load(dossier.id, { silent: true })}
                  />
                </div>
              ) : activeId === "deck" ? (
                <div className="alnua-scroll min-h-0 flex-1 overflow-y-auto p-4 sm:p-6">
                  <RndDeckPanel
                    dossierId={dossier.id}
                    dossierTitle={dossier.title}
                    deckHtmlPath={dossier.deck_html_path}
                    deckPdfPath={dossier.deck_pdf_path}
                    onGenerated={() => void load(dossier.id, { silent: true })}
                  />
                </div>
              ) : activeId === "visuals" ? (
                <div className="alnua-scroll min-h-0 flex-1 overflow-y-auto p-4 sm:p-6">
                  <RndVisualPanel
                    dossierId={dossier.id}
                    dossierTitle={dossier.title}
                    onGenerated={() => void load(dossier.id, { silent: true })}
                  />
                </div>
              ) : activeId === "social" ? (
                <div className="alnua-scroll min-h-0 flex-1 overflow-y-auto p-4 sm:p-6">
                  <RndSocialPanel
                    dossierId={dossier.id}
                    dossierTitle={dossier.title}
                    dossierStatus={dossier.status}
                    ceoStatus={dossier.ceo_status}
                    onUpdated={() => void load(dossier.id, { silent: true })}
                  />
                </div>
              ) : activeId === "ceo" ? (
                <div className="alnua-scroll min-h-0 flex-1 overflow-y-auto p-4 sm:p-6">
                  <RndCeoPanel
                    dossierId={dossier.id}
                    dossierTitle={dossier.title}
                    dossierStatus={dossier.status}
                    onUpdated={() => void load(dossier.id, { silent: true })}
                  />
                </div>
              ) : activeId === "product" ? (
                <div className="alnua-scroll min-h-0 flex-1 overflow-y-auto p-4 sm:p-6">
                  <RndProductPanel
                    dossierId={dossier.id}
                    dossierTitle={dossier.title}
                    dossierStatus={dossier.status}
                    ceoStatus={dossier.ceo_status}
                    onUpdated={() => void load(dossier.id, { silent: true })}
                  />
                </div>
              ) : (
                <div className="alnua-scroll min-h-0 flex-1 overflow-y-auto p-4 sm:p-6">
                  <RndPipelinePanel dossierId={dossier.id} onNavigateTab={handleNavigateTab} />
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}
