"use client";

import { FileText, MessageSquare, Plus, Sparkles } from "lucide-react";
import { AlnuaStar } from "@/components/brand/alnua-star";
import { useCooStore } from "@/store/coo-store";
import { cn } from "@/lib/utils";

const QUICK_ACTIONS = [
  { icon: Plus, label: "Nouvelle mission" },
  { icon: FileText, label: "Rapport d'équipe" },
  { icon: Sparkles, label: "Analyse projet" },
  { icon: MessageSquare, label: "Automatisation" },
];

export function MockupBottomBar() {
  const openDrawer = useCooStore((s) => s.openDrawer);
  const setPrefillMessage = useCooStore((s) => s.setPrefillMessage);

  return (
    <div className="pointer-events-none fixed bottom-0 left-0 right-0 z-40 flex justify-center pb-4 sm:pb-5">
      <div className="pointer-events-auto flex items-center gap-2 rounded-full border border-bronze-faint bg-obsidian-deep/90 px-3 py-2 shadow-2xl backdrop-blur-xl sm:gap-4 sm:px-5">
        <button
          type="button"
          onClick={() => {
            setPrefillMessage("Que dois-je faire aujourd'hui ?");
            openDrawer();
          }}
          className="group relative flex h-10 w-10 items-center justify-center rounded-full bg-obsidian-2 transition-colors hover:bg-obsidian-3"
          aria-label="Commande centrale"
        >
          <AlnuaStar className="h-5 w-5 text-copper transition-colors group-hover:text-copper-light" />
          <span className="absolute inset-0 rounded-full opacity-0 shadow-glow transition-opacity group-hover:opacity-60" />
        </button>

        <input
          type="text"
          readOnly
          placeholder="Que souhaitez-vous faire aujourd'hui ?"
          onClick={() => {
            setPrefillMessage("Que dois-je faire aujourd'hui ?");
            openDrawer();
          }}
          className="hidden w-48 cursor-pointer bg-transparent text-xs text-ivoire placeholder:text-titane/50 focus:outline-none sm:block md:w-64"
        />

        <div className="flex items-center gap-1 sm:gap-2">
          {QUICK_ACTIONS.map((action) => (
            <button
              key={action.label}
              type="button"
              onClick={() => {
                setPrefillMessage(`${action.label} : `);
                openDrawer();
              }}
              className={cn(
                "flex items-center gap-1.5 rounded-full border border-bronze-faint px-2.5 py-1.5 text-[10px] text-titane/80 transition-colors hover:border-bronze/40 hover:text-bronze-bright",
                "sm:px-3 sm:text-[11px]",
              )}
            >
              <action.icon className="h-3 w-3 sm:h-3.5 sm:w-3.5" />
              <span className="hidden sm:inline">{action.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
