"use client";

import { SectionPreview, SectionStatusIcon } from "@/components/rnd/rnd-section-preview";
import type { RndDossierDetail, RndDossierEvent } from "@/lib/rnd-dossier";
import { cn } from "@/lib/utils";

/* Extrait de rnd-dossier-workspace.tsx (correctif Phase 27, ROADMAP.md) —
   le corps liste-sections + journal + preview, sorti pour être réutilisé à la
   fois par rnd-dossier-workspace.tsx (/rd, inchangé) et
   rnd-v2/dossier-detail-view.tsx (nouvel onglet "Sections"). Comportement
   identique à l'original, seule la source de vérité (`activeSection`) est
   maintenant contrôlée par le parent au lieu d'un état local. */

export interface RndDossierSectionsPanelProps {
  dossier: RndDossierDetail;
  events: RndDossierEvent[];
  activeSection: string | null;
  onSelectSection: (key: string) => void;
  onUpdated: () => void;
}

export function RndDossierSectionsPanel({
  dossier,
  events,
  activeSection,
  onSelectSection,
  onUpdated,
}: RndDossierSectionsPanelProps) {
  const currentSection = dossier.sections.find((s) => s.section_key === activeSection);

  return (
    <div className="grid min-h-0 flex-1 gap-4 lg:grid-cols-5">
      <aside className="space-y-1 overflow-y-auto lg:col-span-2">
        <p className="label-caps mb-2 text-titanium/50">Sections</p>
        {dossier.sections.map((sec) => (
          <button
            key={sec.id}
            type="button"
            onClick={() => onSelectSection(sec.section_key)}
            className={cn(
              "flex w-full items-center gap-2 rounded-lg px-3 py-2 text-left text-xs transition",
              activeSection === sec.section_key
                ? "bg-copper/15 text-copper"
                : "text-titanium/70 hover:bg-obsidian-deep/50 hover:text-ivory/80"
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
          <SectionPreview section={currentSection} dossierId={dossier.id} onUpdated={onUpdated} />
        ) : (
          <p className="text-sm text-titanium/50">Aucune section sélectionnée.</p>
        )}
      </div>
    </div>
  );
}
