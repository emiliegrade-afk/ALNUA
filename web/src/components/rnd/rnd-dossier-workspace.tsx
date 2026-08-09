"use client";

import { useCallback, useEffect, useState } from "react";
import { FileText, Loader2, MessageSquare, X } from "lucide-react";
import { RndCommitteePanel } from "@/components/rnd/rnd-committee-panel";
import { RndDossierSectionsPanel } from "@/components/rnd/rnd-dossier-sections-panel";
import { RndFinancePanel } from "@/components/rnd/rnd-finance-panel";
import {
  fetchRndDossier,
  fetchRndDossierEvents,
  type RndDossierDetail,
  type RndDossierEvent,
  type RndDossierListItem,
} from "@/lib/rnd-dossier";
import { cn } from "@/lib/utils";

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
            className="rounded-lg p-1 text-titanium/50 hover:bg-obsidian/50 hover:text-ivory"
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

      <div className="flex w-fit gap-1 rounded-lg border border-copper/15 bg-obsidian-deep/40 p-1">
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
        <RndDossierSectionsPanel
          dossier={dossier}
          events={events}
          activeSection={activeSection}
          onSelectSection={setActiveSection}
          onUpdated={() => load(dossier.id)}
        />
      )}
    </div>
  );
}
