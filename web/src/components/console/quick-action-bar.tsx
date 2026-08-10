"use client";

import Link from "next/link";
import { Activity, BarChart3, Sparkles, Workflow } from "lucide-react";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { useQuickCaptureStore } from "@/store/quick-capture-store";
import { useCooStore } from "@/store/coo-store";
import { ROUTES } from "@/lib/routes";

const actionClass =
  "flex items-center gap-1.5 rounded-xl px-2.5 py-1.5 text-[11px] text-titane/70 transition-colors hover:bg-obsidian hover:text-ivoire sm:text-xs";

/**
 * Barre d'action persistante des maquettes — une marque centrale en halo,
 * « Que souhaitez-vous faire aujourd'hui ? », et deux actions de chaque côté.
 * Chrome global (les 3 écrans de référence la portent), donc montée dans
 * ConsoleShell à côté de la sidebar/topbar, pas page par page.
 */
export function QuickActionBar() {
  const openDrawer = useCooStore((s) => s.openDrawer);
  const setCaptureOpen = useQuickCaptureStore((s) => s.setOpen);

  return (
    <div className="pointer-events-none sticky bottom-4 z-20 mt-8 flex justify-center px-4">
      <div className="pointer-events-auto flex w-full max-w-3xl items-center gap-2 rounded-full border border-bronze-faint bg-obsidian-deep/90 px-3 py-2 shadow-[0_8px_32px_rgba(0,0,0,0.5)] backdrop-blur-xl sm:gap-3 sm:px-4">
        <span className="hidden flex-1 whitespace-nowrap pl-2 text-xs text-titane/60 min-[900px]:inline">
          Que souhaitez-vous faire aujourd&apos;hui ?
        </span>

        <button
          type="button"
          onClick={openDrawer}
          aria-label="Ouvrir les assistants Aria et Nadia"
          className="group relative -my-4 flex h-16 w-16 shrink-0 items-center justify-center rounded-full"
        >
          <span
            className="pointer-events-none absolute inset-0 rounded-full opacity-70 transition-opacity duration-500 group-hover:opacity-100"
            style={{
              background:
                "radial-gradient(circle, rgba(217,168,143,0.35) 0%, rgba(224,155,106,0.12) 45%, transparent 70%)",
            }}
          />
          <span className="pointer-events-none absolute inset-2 rounded-full border border-bronze/30" />
          <span className="pointer-events-none absolute inset-4 rounded-full border border-bronze/15" />
          <AlnuaStar size={38} glow />
        </button>

        {/* Maquette : les 4 actions sont groupées à droite de l'orbe, pas
            réparties de part et d'autre. */}
        <div className="flex flex-1 items-center justify-end gap-0.5 sm:gap-1.5">
          <button type="button" onClick={() => setCaptureOpen(true)} className={actionClass}>
            <Sparkles className="h-3.5 w-3.5 shrink-0" />
            <span className="hidden sm:inline">Nouvelle mission</span>
          </button>
          <Link href={ROUTES.activity} className={actionClass}>
            <Activity className="h-3.5 w-3.5 shrink-0" />
            <span className="hidden sm:inline">Rapport d&apos;équipe</span>
          </Link>
          <Link href={ROUTES.analytics} className={actionClass}>
            <BarChart3 className="h-3.5 w-3.5 shrink-0" />
            <span className="hidden sm:inline">Analyse projet</span>
          </Link>
          <button type="button" onClick={openDrawer} className={actionClass}>
            <Workflow className="h-3.5 w-3.5 shrink-0" />
            <span className="hidden sm:inline">Automatisation</span>
          </button>
        </div>
      </div>
    </div>
  );
}
