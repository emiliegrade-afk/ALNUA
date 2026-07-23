"use client";

import { RefreshCw } from "lucide-react";
import type { IdeTreeEntry, IdeWorkspace } from "@/lib/ide-api";
import type { SidebarView } from "./ide-activity-bar";
import { IdeFileTree } from "./ide-file-tree";

export function IdeSidebar({
  view,
  workspace,
  workspaces,
  rootEntries,
  selectedPath,
  fileFilter,
  expanded,
  readOnly,
  activeAgent,
  onWorkspaceChange,
  onFilterChange,
  onSelectFile,
  onExpand,
  onRefresh,
}: {
  view: SidebarView;
  workspace: string;
  workspaces: IdeWorkspace[];
  rootEntries: IdeTreeEntry[];
  selectedPath: string | null;
  fileFilter: string;
  expanded: Record<string, boolean>;
  readOnly: boolean;
  activeAgent?: string;
  onWorkspaceChange: (id: string) => void;
  onFilterChange: (q: string) => void;
  onSelectFile: (path: string) => void;
  onExpand: (path: string) => void;
  onRefresh: () => void;
}) {
  const title =
    view === "explorer"
      ? "EXPLORATEUR"
      : view === "search"
        ? "RECHERCHE"
        : "AGENT LIVE";

  return (
    <aside className="flex h-full min-h-0 flex-col bg-obsidian-2/90">
      <div className="flex shrink-0 items-center justify-between border-b border-bronze-faint px-3 py-2">
        <span className="font-mono text-[10px] tracking-[0.2em] text-titane/50">
          {title}
        </span>
        <button
          type="button"
          onClick={onRefresh}
          className="rounded p-1 text-titane/50 transition-colors hover:bg-obsidian hover:text-ivoire"
          title="Actualiser"
        >
          <RefreshCw className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="shrink-0 space-y-2 border-b border-bronze-faint px-2 py-2">
        <select
          value={workspace}
          onChange={(e) => onWorkspaceChange(e.target.value)}
          className="w-full rounded-md border border-bronze-faint bg-obsidian px-2 py-1.5 font-mono text-[11px] text-ivoire outline-none focus:border-bronze/50"
        >
          {workspaces.map((w) => (
            <option key={w.id} value={w.id}>
              {w.label}
              {w.readOnly ? " · lecture" : ""}
              {w.active ? " ●" : ""}
            </option>
          ))}
        </select>
        {readOnly ? (
          <p className="rounded bg-amber-500/10 px-2 py-1 text-[10px] text-amber-200/90">
            Lecture seule — agent actif
          </p>
        ) : null}
        {activeAgent ? (
          <p className="rounded bg-emerald-500/10 px-2 py-1 text-[10px] text-emerald-300/90">
            {activeAgent}
          </p>
        ) : null}
      </div>

      {(view === "explorer" || view === "search") && (
        <div className="shrink-0 px-2 py-2">
          <input
            value={fileFilter}
            onChange={(e) => onFilterChange(e.target.value)}
            placeholder={view === "search" ? "Filtrer les fichiers…" : "Fichiers…"}
            className="w-full rounded-md border border-bronze-faint bg-obsidian px-2 py-1.5 font-mono text-[11px] text-ivoire outline-none placeholder:text-titane/35 focus:border-bronze/50"
          />
        </div>
      )}

      <div className="min-h-0 flex-1 overflow-y-auto alnua-scroll">
        {view === "agent" ? (
          <div className="space-y-2 p-3 text-[11px] text-titane/70">
            <p>
              Surveille le travail de Théo en temps réel dans le panneau du bas
              · onglet <strong className="text-ivoire">Agent</strong>.
            </p>
            <p>
              Bascule sur <strong className="text-ivoire">Agent en cours</strong>{" "}
              dans le workspace pour voir son worktree.
            </p>
          </div>
        ) : (
          <IdeFileTree
            workspace={workspace}
            entries={rootEntries}
            selectedPath={selectedPath}
            filter={fileFilter}
            expanded={expanded}
            onSelectFile={onSelectFile}
            onExpand={onExpand}
          />
        )}
      </div>
    </aside>
  );
}
