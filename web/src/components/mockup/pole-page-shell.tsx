"use client";

import { AnimatePresence, motion } from "framer-motion";
import { cn } from "@/lib/utils";

export interface PoleTabDef {
  id: string;
  label: string;
}

interface PolePageShellProps {
  tabs: PoleTabDef[];
  activeTab: string;
  onTabChange: (id: string) => void;
  children: React.ReactNode;
  layoutId?: string;
}

export function PolePageShell({
  tabs,
  activeTab,
  onTabChange,
  children,
  layoutId = "pole-tab-underline",
}: PolePageShellProps) {
  return (
    <div className="space-y-3 pb-24">
      <nav className="flex gap-1 overflow-x-auto border-b border-bronze-faint">
        {tabs.map((t) => (
          <button
            key={t.id}
            type="button"
            onClick={() => onTabChange(t.id)}
            className={cn(
              "relative shrink-0 px-3 py-2.5 text-[11px] font-medium transition-colors",
              activeTab === t.id ? "text-copper" : "text-titane/55 hover:text-ivoire/80",
            )}
          >
            {t.label}
            {activeTab === t.id ? (
              <motion.span
                layoutId={layoutId}
                className="absolute inset-x-1 bottom-0 h-0.5 rounded-full bg-copper"
                transition={{ type: "spring", stiffness: 380, damping: 30 }}
              />
            ) : null}
          </button>
        ))}
      </nav>

      <AnimatePresence mode="wait">
        <motion.div
          key={activeTab}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -6 }}
          transition={{ duration: 0.25, ease: [0.22, 1, 0.36, 1] }}
        >
          {children}
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

export function PolePlaceholder({
  title,
  onBack,
}: {
  title: string;
  onBack?: () => void;
}) {
  return (
    <div className="rounded-xl border border-bronze-faint bg-obsidian/60 p-10 text-center">
      <p className="font-title text-sm text-ivoire/80">{title}</p>
      <p className="mt-2 text-xs text-titane/50">
        Maquette visuelle — branchement prévu (Phase 38 ROADMAP).
      </p>
      {onBack ? (
        <button
          type="button"
          onClick={onBack}
          className="mt-4 text-[11px] text-copper hover:underline"
        >
          ← Retour
        </button>
      ) : null}
    </div>
  );
}

export const poleFadeUp = {
  hidden: { opacity: 0, y: 12 },
  show: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.05, duration: 0.35, ease: [0.22, 1, 0.36, 1] as const },
  }),
};
