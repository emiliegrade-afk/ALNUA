"use client";

import Link from "next/link";
import {
  Bot,
  Files,
  Home,
  PanelBottom,
  PanelLeft,
  PanelRight,
  Radio,
  Search,
  Sparkles,
} from "lucide-react";
import { cn } from "@/lib/utils";

export type SidebarView = "explorer" | "search" | "agent";

export function IdeActivityBar({
  sidebarView,
  sidebarOpen,
  aiOpen,
  bottomOpen,
  onViewChange,
  onToggleSidebar,
  onToggleAi,
  onToggleBottom,
}: {
  sidebarView: SidebarView;
  sidebarOpen: boolean;
  aiOpen: boolean;
  bottomOpen: boolean;
  onViewChange: (view: SidebarView) => void;
  onToggleSidebar: () => void;
  onToggleAi: () => void;
  onToggleBottom: () => void;
}) {
  const items: Array<{
    id: SidebarView;
    icon: typeof Files;
    label: string;
  }> = [
    { id: "explorer", icon: Files, label: "Explorateur" },
    { id: "search", icon: Search, label: "Recherche" },
    { id: "agent", icon: Radio, label: "Agent live" },
  ];

  return (
    <aside className="flex w-12 shrink-0 flex-col border-r border-bronze-faint bg-obsidian-deep">
      <div className="flex flex-1 flex-col items-center gap-1 py-2">
        {items.map(({ id, icon: Icon, label }) => (
          <button
            key={id}
            type="button"
            title={label}
            onClick={() => {
              if (sidebarView === id && sidebarOpen) onToggleSidebar();
              else {
                onViewChange(id);
                if (!sidebarOpen) onToggleSidebar();
              }
            }}
            className={cn(
              "relative flex h-10 w-10 items-center justify-center rounded-lg transition-colors",
              sidebarOpen && sidebarView === id
                ? "text-bronze-bright"
                : "text-titane/55 hover:text-ivoire",
            )}
          >
            {sidebarOpen && sidebarView === id ? (
              <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-bronze" />
            ) : null}
            <Icon className="h-[18px] w-[18px]" />
          </button>
        ))}
      </div>

      <div className="flex flex-col items-center gap-1 border-t border-bronze-faint py-2">
        <button
          type="button"
          title="Terminal"
          onClick={onToggleBottom}
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-lg transition-colors",
            bottomOpen ? "text-bronze-bright" : "text-titane/55 hover:text-ivoire",
          )}
        >
          <PanelBottom className="h-4 w-4" />
        </button>
        <button
          type="button"
          title="Assistant IA"
          onClick={onToggleAi}
          className={cn(
            "flex h-9 w-9 items-center justify-center rounded-lg transition-colors",
            aiOpen ? "text-bronze-bright" : "text-titane/55 hover:text-ivoire",
          )}
        >
          <Sparkles className="h-4 w-4" />
        </button>
        <button
          type="button"
          title="Masquer sidebar"
          onClick={onToggleSidebar}
          className="flex h-9 w-9 items-center justify-center rounded-lg text-titane/55 transition-colors hover:text-ivoire"
        >
          <PanelLeft className="h-4 w-4" />
        </button>
        <Link
          href="/"
          title="Retour au Hub"
          className="flex h-9 w-9 items-center justify-center rounded-lg text-titane/55 transition-colors hover:text-ivoire"
        >
          <Home className="h-4 w-4" />
        </Link>
      </div>
    </aside>
  );
}

export function IdeAiToggleStrip({ onOpen }: { onOpen: () => void }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="flex w-9 shrink-0 flex-col items-center justify-center gap-1 border-l border-bronze-faint bg-obsidian-deep text-titane/50 transition-colors hover:bg-obsidian-2 hover:text-bronze-bright"
      title="Ouvrir l'assistant"
    >
      <Bot className="h-4 w-4" />
      <PanelRight className="h-3 w-3 opacity-50" />
    </button>
  );
}
