"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchLibraryEntries, type LibraryEntry } from "@/lib/library-api";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { getAgentById } from "@/lib/agent-bureau";
import type { Project } from "@/lib/types";
import { C } from "../app-v2/shared";
import { hash } from "./mock-data";

/* Documentation Robotique — même vraie bibliothèque que App/Gaming
 * (fetchLibraryEntries, bureau "robo"), catégories orientées hardware
 * dérivées de façon stable (pas de champ "catégorie" réel dans ce système). */

const CATEGORIES = ["Datasheets", "Schémas", "PCB", "Fusion360", "SolidWorks", "ESP32", "RPi", "Normes CE", "Protocoles", "Drivers"] as const;

function categoryOf(entry: LibraryEntry): string {
  return CATEGORIES[hash(entry.id) % CATEGORIES.length];
}

function relTime(iso: string) {
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
  if (days <= 0) return "aujourd'hui";
  if (days === 1) return "hier";
  return `il y a ${days} j`;
}

export function DocumentationTab({ projects }: { projects: Project[] }) {
  const [entries, setEntries] = useState<LibraryEntry[] | "loading" | "error">("loading");
  const [filter, setFilter] = useState<(typeof CATEGORIES)[number] | "Toutes">("Toutes");

  useEffect(() => {
    let cancelled = false;
    fetchLibraryEntries({ bureau: "robo", limit: 100 })
      .then((r) => {
        if (!cancelled) setEntries(r.entries ?? []);
      })
      .catch(() => {
        if (!cancelled) setEntries("error");
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    if (!Array.isArray(entries)) return [];
    const sorted = [...entries].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
    return filter === "Toutes" ? sorted : sorted.filter((e) => categoryOf(e) === filter);
  }, [entries, filter]);

  const categoryCounts = useMemo(() => {
    if (!Array.isArray(entries)) return {};
    const counts: Record<string, number> = {};
    for (const e of entries) counts[categoryOf(e)] = (counts[categoryOf(e)] ?? 0) + 1;
    return counts;
  }, [entries]);

  if (entries === "loading") {
    return (
      <div className="flex min-h-[220px] flex-1 items-center justify-center rounded-xl text-[11px]" style={{ border: `1px solid ${C.line}`, color: C.faint }}>
        Chargement de la documentation…
      </div>
    );
  }
  if (entries === "error") {
    return (
      <div className="flex min-h-[220px] flex-1 items-center justify-center rounded-xl text-[11px]" style={{ border: `1px solid ${C.line}`, color: C.faint }}>
        La bibliothèque du Hub est injoignable.
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto pb-2">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            DOCUMENTATION — HARDWARE ({entries.length})
          </p>
          {projects[0] ? (
            <p className="text-[10px]" style={{ color: C.dim }}>
              {projects[0].name}
            </p>
          ) : null}
        </div>
      </div>

      <div className="flex gap-2 overflow-x-auto">
        {(["Toutes", ...CATEGORIES] as const).map((c) => (
          <button
            key={c}
            type="button"
            onClick={() => setFilter(c)}
            className="shrink-0 rounded-full border px-3 py-1 text-[10px]"
            style={{
              borderColor: filter === c ? C.copper : "rgba(192,138,114,.2)",
              background: filter === c ? "rgba(192,138,114,.15)" : "transparent",
              color: filter === c ? C.copperLight : C.warm,
            }}
          >
            {c}
            {c !== "Toutes" ? <span className="ml-1" style={{ color: C.faint }}>{categoryCounts[c] ?? 0}</span> : null}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <div className="flex min-h-[180px] flex-1 items-center justify-center rounded-xl border text-[11px]" style={{ borderColor: C.line, color: C.faint }}>
          Aucun document dans cette catégorie.
        </div>
      ) : (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(250px,1fr))] gap-2.5">
          {filtered.map((e) => {
            const author = e.agent_id ? getAgentById(e.agent_id) : undefined;
            return (
              <div key={e.id} className="flex flex-col gap-1.5 rounded-xl border p-3" style={{ borderColor: C.line, background: "rgba(19,22,27,.55)" }}>
                <div className="flex items-center justify-between gap-2">
                  <span className="rounded-full border px-1.5 py-px text-[8px]" style={{ borderColor: "rgba(192,138,114,.22)", color: C.copperLight }}>
                    {categoryOf(e)}
                  </span>
                  {e.timing === "now" ? (
                    <span className="text-[8px]" style={{ color: C.online }}>
                      Épinglé
                    </span>
                  ) : null}
                </div>
                <p className="truncate text-[11.5px] font-medium" style={{ color: C.ivory }}>
                  {e.title}
                </p>
                <p className="line-clamp-2 text-[9.5px]" style={{ color: C.dim }}>
                  {e.summary}
                </p>
                <div className="flex items-center justify-between border-t pt-1.5 text-[9px]" style={{ borderColor: C.lineSoft, color: C.faint }}>
                  {author ? (
                    <span className="flex items-center gap-1">
                      <AgentAvatar agentId={author.id} name={author.name} size={14} />
                      {author.name.split(" ")[0]}
                    </span>
                  ) : (
                    <span>—</span>
                  )}
                  <span>{relTime(e.created_at)}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
