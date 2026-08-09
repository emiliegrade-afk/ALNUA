"use client";

import { format, parseISO } from "date-fns";
import { fr } from "date-fns/locale";
import { ChevronDown, ChevronRight } from "lucide-react";
import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Release } from "@/lib/releases-api";

interface ReleasesListProps {
  releases: Release[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

function formatReleaseDate(dateStr: string | null, fallback: string): string {
  const raw = dateStr ?? fallback;
  try {
    return format(parseISO(raw.slice(0, 10)), "d MMM yyyy", { locale: fr });
  } catch {
    return raw.slice(0, 10);
  }
}

function StatusBadge({ status }: { status: Release["status"] }) {
  return (
    <Badge
      variant="outline"
      className={cn(
        "text-[10px] font-medium uppercase tracking-wide",
        status === "published"
          ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-300"
          : "border-copper/20 bg-obsidian/50 text-titanium"
      )}
    >
      {status === "published" ? "publiée" : "brouillon"}
    </Badge>
  );
}

export function ReleasesList({
  releases,
  selectedId,
  onSelect,
}: ReleasesListProps) {
  const grouped = useMemo(() => {
    const map = new Map<string, { name: string; items: Release[] }>();
    for (const release of releases) {
      const key = release.project_id;
      const name = release.project_name ?? "Projet";
      const existing = map.get(key);
      if (existing) {
        existing.items.push(release);
      } else {
        map.set(key, { name, items: [release] });
      }
    }
    return Array.from(map.entries()).sort((a, b) =>
      a[1].name.localeCompare(b[1].name, "fr")
    );
  }, [releases]);

  const [openProjects, setOpenProjects] = useState<Set<string>>(() => {
    const ids = new Set<string>();
    grouped.forEach(([id]) => ids.add(id));
    return ids;
  });

  function toggleProject(projectId: string) {
    setOpenProjects((prev) => {
      const next = new Set(prev);
      if (next.has(projectId)) next.delete(projectId);
      else next.add(projectId);
      return next;
    });
  }

  if (releases.length === 0) {
    return (
      <div className="rounded-xl border border-copper/15 bg-obsidian-deep/40 p-6 text-center text-sm text-titanium">
        Aucune release pour l&apos;instant.
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {grouped.map(([projectId, { name, items }]) => {
        const open = openProjects.has(projectId);
        return (
          <div
            key={projectId}
            className="overflow-hidden rounded-xl border border-copper/15 bg-obsidian-deep/40"
          >
            <button
              type="button"
              onClick={() => toggleProject(projectId)}
              className="flex w-full items-center gap-2 px-4 py-3 text-left text-sm font-medium text-ivory hover:bg-obsidian-deep/50"
            >
              {open ? (
                <ChevronDown className="h-4 w-4 shrink-0 text-titanium" />
              ) : (
                <ChevronRight className="h-4 w-4 shrink-0 text-titanium" />
              )}
              {name}
              <span className="ml-auto text-xs font-normal text-titanium">
                {items.length}
              </span>
            </button>
            {open && (
              <ul className="border-t border-copper/15">
                {items.map((release) => {
                  const active = release.id === selectedId;
                  return (
                    <li key={release.id}>
                      <button
                        type="button"
                        onClick={() => onSelect(release.id)}
                        className={cn(
                          "flex w-full flex-col gap-1.5 px-4 py-3 text-left transition-colors",
                          active
                            ? "bg-copper/10 text-ivory"
                            : "text-titanium hover:bg-obsidian-deep/50 hover:text-ivory"
                        )}
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-mono text-sm font-semibold text-copper-glow">
                            v{release.version}
                          </span>
                          <StatusBadge status={release.status} />
                        </div>
                        <span className="text-xs text-titanium">
                          {formatReleaseDate(
                            release.release_date,
                            release.created_at
                          )}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        );
      })}
    </div>
  );
}
