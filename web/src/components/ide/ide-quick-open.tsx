"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { FileCode, Search } from "lucide-react";
import { cn } from "@/lib/utils";

export function IdeQuickOpen({
  open,
  files,
  onClose,
  onSelect,
}: {
  open: boolean;
  files: string[];
  onClose: () => void;
  onSelect: (path: string) => void;
}) {
  const [query, setQuery] = useState("");
  const [index, setIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const results = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return files.slice(0, 20);
    return files
      .filter((f) => f.toLowerCase().includes(q))
      .slice(0, 20);
  }, [files, query]);

  useEffect(() => {
    if (open) {
      setQuery("");
      setIndex(0);
      requestAnimationFrame(() => inputRef.current?.focus());
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-start justify-center bg-obsidian-deep/70 pt-[12vh] backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="w-full max-w-xl overflow-hidden rounded-xl border border-bronze-faint bg-obsidian-2 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-2 border-b border-bronze-faint px-3 py-2.5">
          <Search className="h-4 w-4 text-titane/50" />
          <input
            ref={inputRef}
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setIndex(0);
            }}
            placeholder="Rechercher un fichier…"
            className="min-w-0 flex-1 bg-transparent font-mono text-sm text-ivoire outline-none placeholder:text-titane/40"
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") {
                e.preventDefault();
                setIndex((i) => Math.min(i + 1, results.length - 1));
              } else if (e.key === "ArrowUp") {
                e.preventDefault();
                setIndex((i) => Math.max(i - 1, 0));
              } else if (e.key === "Enter" && results[index]) {
                onSelect(results[index]);
                onClose();
              }
            }}
          />
          <kbd className="rounded border border-bronze-faint px-1.5 py-0.5 font-mono text-[10px] text-titane/50">
            Esc
          </kbd>
        </div>
        <ul className="max-h-72 overflow-y-auto py-1">
          {results.length === 0 ? (
            <li className="px-4 py-6 text-center text-sm text-titane/50">
              Aucun fichier
            </li>
          ) : (
            results.map((path, i) => (
              <li key={path}>
                <button
                  type="button"
                  className={cn(
                    "flex w-full items-center gap-2 px-3 py-2 text-left font-mono text-xs transition-colors",
                    i === index
                      ? "bg-bronze/15 text-bronze-bright"
                      : "text-titane/80 hover:bg-obsidian",
                  )}
                  onMouseEnter={() => setIndex(i)}
                  onClick={() => {
                    onSelect(path);
                    onClose();
                  }}
                >
                  <FileCode className="h-3.5 w-3.5 shrink-0 opacity-60" />
                  <span className="truncate">{path}</span>
                </button>
              </li>
            ))
          )}
        </ul>
      </div>
    </div>
  );
}
