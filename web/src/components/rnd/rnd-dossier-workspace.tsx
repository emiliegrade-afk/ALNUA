"use client";

import { useCallback, useEffect, useState } from "react";
import {
  CheckCircle2,
  Circle,
  FileText,
  Loader2,
  MessageSquare,
  X,
} from "lucide-react";
import { RndCommitteePanel } from "@/components/rnd/rnd-committee-panel";
import { RndFinancePanel } from "@/components/rnd/rnd-finance-panel";
import { RndSectionActions } from "@/components/rnd/rnd-section-actions";
import {
  fetchRndDossier,
  fetchRndDossierEvents,
  type RndDossierDetail,
  type RndDossierEvent,
  type RndDossierListItem,
  type RndDossierSection,
} from "@/lib/rnd-dossier";
import { cn } from "@/lib/utils";

function SectionStatusIcon({ status }: { status: string }) {
  if (status === "validated") {
    return <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />;
  }
  if (status === "needs_revision") {
    return <Circle className="h-3.5 w-3.5 text-amber-400" />;
  }
  if (status === "under_review") {
    return <Circle className="h-3.5 w-3.5 text-copper/70" />;
  }
  return <Circle className="h-3.5 w-3.5 text-titanium/40" />;
}

function SectionPreview({
  section,
  dossierId,
  onUpdated,
}: {
  section: RndDossierSection;
  dossierId: string;
  onUpdated: () => void;
}) {
  return (
    <section className="rounded-xl border border-copper/10 bg-white/[0.02] p-4">
      <div className="mb-2 flex items-center gap-2">
        <SectionStatusIcon status={section.status} />
        <h3 className="text-sm font-semibold text-ivory/90">{section.title}</h3>
        <span className="ml-auto text-[10px] text-titanium/50">{section.status}</span>
      </div>
      <div className="prose prose-invert max-w-none text-sm leading-relaxed text-titanium/80">
        <pre className="whitespace-pre-wrap font-sans text-sm">{section.content_md}</pre>
      </div>
      <RndSectionActions
        dossierId={dossierId}
        section={section}
        onUpdated={onUpdated}
      />
    </section>
  );
}

interface RndDossierWorkspaceProps {
  dossierItem: RndDossierListItem | null;
  onClose?: () => void;
}

export function RndDossierWorkspace({ dossierItem, onClose }: RndDossierWorkspaceProps) {
  const [dossier, setDossier] = useState<RndDossierDetail | null>(null);
  const [events, setEvents] = useState<RndDossierEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeSection, setActiveSection] = useState<string | null>(null);
  const [workspaceTab, setWorkspaceTab] = useState<"sections" | "committee">("sections");

  const load = useCallback(async (id: string, opts?: { silent?: boolean }) => {
    if (!opts?.silent) setLoading(true);
    try {
      const [d, ev] = await Promise.all([
        fetchRndDossier(id),
        fetchRndDossierEvents(id),
      ]);
      setDossier(d);
      setEvents(ev);
      setActiveSection((prev) => prev ?? d.sections[0]?.section_key ?? null);
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
    if (dossierItem?.id) {
      setActiveSection(null);
      load(dossierItem.id);
    } else {
      setDossier(null);
      setEvents([]);
    }
  }, [dossierItem?.id, load]);

  // Poll while background enrich is running (no finance_json yet).
  useEffect(() => {
    if (!dossier?.id || dossier.finance_json) return;
    const id = dossier.id;
    const timer = window.setInterval(() => {
      void load(id, { silent: true });
    }, 5000);
    const stop = window.setTimeout(() => window.clearInterval(timer), 120_000);
    return () => {
      window.clearInterval(timer);
      window.clearTimeout(stop);
    };
  }, [dossier?.id, dossier?.finance_json, load]);

  if (!dossierItem) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 text-center">
        <FileText className="h-12 w-12 text-copper/20" />
        <p className="text-sm text-titanium/60">
          Sélectionne un dossier pour voir les sections et le journal d&apos;activité.
        </p>
      </div>
    );
  }

  if (loading || !dossier) {
    return (
      <div className="flex h-full items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-copper/50" />
      </div>
    );
  }

  const currentSection = dossier.sections.find((s) => s.section_key === activeSection);

  return (
    <div className="flex h-full flex-col gap-4 overflow-hidden">
      <div className="flex shrink-0 items-start justify-between gap-3 border-b border-copper/10 pb-4">
        <div>
          <h2 className="font-title text-xl text-ivory">{dossier.title}</h2>
          <p className="mt-1 text-xs text-titanium/60">
            {dossier.slug} · {dossier.sections_validated_count}/{dossier.sections_total_count}{" "}
            sections validées · CEO : {dossier.ceo_status}
          </p>
        </div>
        {onClose ? (
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1 text-titanium/50 hover:bg-white/5 hover:text-ivory"
            aria-label="Fermer"
          >
            <X className="h-4 w-4" />
          </button>
        ) : null}
      </div>

      {dossier.finance_json ? (
        <RndFinancePanel finance={dossier.finance_json} />
      ) : (
        <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-2 text-xs text-amber-200/80">
          Enrichissement en cours — business case et sections LLM arrivent sous ~1 min.
        </div>
      )}

      <div className="flex w-fit gap-1 rounded-lg border border-white/10 bg-white/[0.02] p-1">
        <button
          type="button"
          onClick={() => setWorkspaceTab("sections")}
          className={cn(
            "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition",
            workspaceTab === "sections"
              ? "bg-copper/20 text-copper"
              : "text-titanium/60 hover:text-ivory/80"
          )}
        >
          <FileText className="h-3.5 w-3.5" />
          Sections
        </button>
        <button
          type="button"
          onClick={() => setWorkspaceTab("committee")}
          className={cn(
            "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition",
            workspaceTab === "committee"
              ? "bg-copper/20 text-copper"
              : "text-titanium/60 hover:text-ivory/80"
          )}
        >
          <MessageSquare className="h-3.5 w-3.5" />
          Comité
          {dossier.status === "committee_active" ? (
            <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          ) : null}
        </button>
      </div>

      {workspaceTab === "committee" ? (
        <div className="min-h-0 flex-1">
          <RndCommitteePanel
            dossierId={dossier.id}
            dossierTitle={dossier.title}
            activeSection={activeSection}
            onClosed={() => load(dossier.id)}
          />
        </div>
      ) : (
      <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-5">
        <aside className="space-y-1 overflow-y-auto lg:col-span-2">
          <p className="label-caps mb-2 text-titanium/50">Sections</p>
          {dossier.sections.map((sec) => (
            <button
              key={sec.id}
              type="button"
              onClick={() => setActiveSection(sec.section_key)}
              className={cn(
                "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs transition",
                activeSection === sec.section_key
                  ? "bg-copper/15 text-copper"
                  : "text-titanium/70 hover:bg-white/[0.04] hover:text-ivory/80"
              )}
            >
              <SectionStatusIcon status={sec.status} />
              <span className="truncate">{sec.title}</span>
            </button>
          ))}

          {events.length > 0 ? (
            <div className="mt-6">
              <p className="label-caps mb-2 text-titanium/50">Journal</p>
              <ul className="space-y-1.5 text-[10px] text-titanium/60">
                {events.slice(0, 12).map((ev) => (
                  <li key={ev.id}>
                    <span className="text-copper/80">{ev.actor}</span> — {ev.event_type}
                    {ev.payload?.section_key ? (
                      <span className="text-titanium/40"> ({String(ev.payload.section_key)})</span>
                    ) : null}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </aside>

        <div className="min-h-0 overflow-y-auto lg:col-span-3">
          {currentSection ? (
            <SectionPreview
              section={currentSection}
              dossierId={dossier.id}
              onUpdated={() => load(dossier.id)}
            />
          ) : (
            <p className="text-sm text-titanium/50">Aucune section sélectionnée.</p>
          )}
        </div>
      </div>
      )}
    </div>
  );
}
