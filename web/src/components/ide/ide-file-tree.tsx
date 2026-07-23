"use client";

import { useEffect, useState } from "react";
import { ChevronDown, ChevronRight, FileCode, Folder } from "lucide-react";
import { fetchIdeTree, type IdeTreeEntry } from "@/lib/ide-api";
import { cn } from "@/lib/utils";

function TreeNode({
  workspace,
  entry,
  depth,
  selectedPath,
  filter,
  onSelectFile,
  onExpand,
  expanded,
}: {
  workspace: string;
  entry: IdeTreeEntry;
  depth: number;
  selectedPath: string | null;
  filter: string;
  onSelectFile: (path: string) => void;
  onExpand: (path: string) => void;
  expanded: Record<string, boolean>;
}) {
  const isDir = entry.type === "dir";
  const isOpen = expanded[entry.path] ?? false;
  const [children, setChildren] = useState<IdeTreeEntry[]>([]);
  const [loading, setLoading] = useState(false);

  const q = filter.trim().toLowerCase();
  const nameMatch = !q || entry.name.toLowerCase().includes(q);

  useEffect(() => {
    if (!isDir || !isOpen) return;
    setLoading(true);
    fetchIdeTree(workspace, entry.path)
      .then((r) => setChildren(r.entries))
      .catch(() => setChildren([]))
      .finally(() => setLoading(false));
  }, [workspace, entry.path, isDir, isOpen]);

  if (!isDir && !nameMatch) return null;

  const filteredChildren = children.filter((c) => {
    if (!q) return true;
    if (c.type === "dir") return true;
    return c.name.toLowerCase().includes(q);
  });

  if (isDir && q && !nameMatch && filteredChildren.length === 0 && !isOpen) {
    return null;
  }

  return (
    <div>
      <button
        type="button"
        className={cn(
          "flex w-full items-center gap-1 rounded-sm px-1 py-0.5 text-left font-mono text-[11px] transition-colors hover:bg-bronze/10",
          selectedPath === entry.path && "bg-bronze/15 text-bronze-bright",
        )}
        style={{ paddingLeft: `${depth * 12 + 6}px` }}
        onClick={() => {
          if (isDir) onExpand(entry.path);
          else onSelectFile(entry.path);
        }}
      >
        {isDir ? (
          isOpen ? (
            <ChevronDown className="h-3 w-3 shrink-0 opacity-50" />
          ) : (
            <ChevronRight className="h-3 w-3 shrink-0 opacity-50" />
          )
        ) : (
          <span className="w-3" />
        )}
        {isDir ? (
          <Folder className="h-3 w-3 shrink-0 text-bronze/70" />
        ) : (
          <FileCode className="h-3 w-3 shrink-0 text-titane/60" />
        )}
        <span className="truncate">{entry.name}</span>
      </button>
      {isDir && isOpen ? (
        loading ? (
          <p
            className="py-1 font-mono text-[10px] text-titane/35"
            style={{ paddingLeft: `${(depth + 1) * 12 + 10}px` }}
          >
            …
          </p>
        ) : (
          filteredChildren.map((child) => (
            <TreeNode
              key={child.path}
              workspace={workspace}
              entry={child}
              depth={depth + 1}
              selectedPath={selectedPath}
              filter={filter}
              onSelectFile={onSelectFile}
              onExpand={onExpand}
              expanded={expanded}
            />
          ))
        )
      ) : null}
    </div>
  );
}

export function IdeFileTree({
  workspace,
  entries,
  selectedPath,
  filter,
  expanded,
  onSelectFile,
  onExpand,
}: {
  workspace: string;
  entries: IdeTreeEntry[];
  selectedPath: string | null;
  filter: string;
  expanded: Record<string, boolean>;
  onSelectFile: (path: string) => void;
  onExpand: (path: string) => void;
}) {
  const q = filter.trim().toLowerCase();
  const visible = entries.filter((e) => !q || e.name.toLowerCase().includes(q) || e.type === "dir");

  return (
    <div className="px-1 pb-3">
      {visible.map((entry) => (
        <TreeNode
          key={entry.path}
          workspace={workspace}
          entry={entry}
          depth={0}
          selectedPath={selectedPath}
          filter={filter}
          onSelectFile={onSelectFile}
          onExpand={onExpand}
          expanded={expanded}
        />
      ))}
    </div>
  );
}
