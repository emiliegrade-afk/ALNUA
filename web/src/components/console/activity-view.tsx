"use client";

import { useMemo, useState } from "react";
import { useConsoleData } from "./console-provider";
import { cn } from "@/lib/utils";
import {
  Rocket,
  GitBranch,
  Lightbulb,
  ShieldAlert,
  Sparkles,
  Activity as ActivityIcon,
  Filter,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";

const KIND_META: Record<string, { icon: LucideIcon; color: string; bg: string; ring: string; label: string }> = {
  ship: { icon: Rocket, color: "text-bronze-bright", bg: "bg-bronze/15", ring: "ring-bronze/30", label: "Livraison" },
  decide: { icon: GitBranch, color: "text-cuivre", bg: "bg-cuivre/15", ring: "ring-cuivre/30", label: "Décision" },
  research: { icon: Lightbulb, color: "text-glow", bg: "bg-glow/15", ring: "ring-glow/30", label: "Recherche" },
  alert: { icon: ShieldAlert, color: "text-red-400", bg: "bg-red-500/15", ring: "ring-red-400/30", label: "Alerte" },
  create: { icon: Sparkles, color: "text-bronze-bright", bg: "bg-bronze/15", ring: "ring-bronze/30", label: "Création" },
};

const FILTERS = ["Tous", "Livraison", "Décision", "Recherche", "Alerte", "Création"] as const;

export function ActivityView() {
  const { activityFeed } = useConsoleData();
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("Tous");

  const filtered = useMemo(() => {
    if (filter === "Tous") return activityFeed;
    const kindMap: Record<string, string> = {
      Livraison: "ship",
      Décision: "decide",
      Recherche: "research",
      Alerte: "alert",
      Création: "create",
    };
    return activityFeed.filter((a) => a.kind === kindMap[filter]);
  }, [filter, activityFeed]);

  return (
    <div className="space-y-5">
      {/* Stats summary */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {(["ship", "decide", "research", "alert", "create"] as const).map((k) => {
          const meta = KIND_META[k];
          const Icon = meta.icon;
          const count = activityFeed.filter((a) => a.kind === k).length;
          return (
            <div
              key={k}
              className="rounded-xl border border-bronze-faint bg-obsidian/70 p-4 flex items-center gap-3"
            >
              <div className={cn("flex h-9 w-9 items-center justify-center rounded-lg ring-1", meta.bg, meta.ring)}>
                <Icon className={cn("h-4 w-4", meta.color)} />
              </div>
              <div>
                <div className="text-lg font-bold text-ivoire">{count}</div>
                <div className="text-[10px] uppercase tracking-wide text-titane/50">
                  {meta.label}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Filter bar */}
      <div className="flex items-center gap-1.5 overflow-x-auto alnua-scroll pb-1">
        <Filter className="h-3.5 w-3.5 text-titane/50 shrink-0 mr-1" />
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={cn(
              "shrink-0 px-3 h-8 rounded-md text-xs font-medium transition-colors",
              filter === f
                ? "bg-bronze text-obsidian-deep"
                : "text-titane/65 hover:text-ivoire hover:bg-obsidian"
            )}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Timeline */}
      <div className="rounded-2xl border border-bronze-faint bg-obsidian/70 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4 border-b border-bronze-faint bg-obsidian-deep/50">
          <div className="flex items-center gap-2.5">
            <span className="relative flex h-2.5 w-2.5">
              <span className="absolute inline-flex h-full w-full rounded-full bg-bronze opacity-75 animate-ping" />
              <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-bronze-bright" />
            </span>
            <h2 className="text-sm font-semibold tracking-wide text-ivoire">
              Flux d&apos;activité — temps réel
            </h2>
          </div>
          <span className="text-[10px] uppercase tracking-[0.2em] text-titane/50">
            {filtered.length} événements
          </span>
        </div>

        <ul className="divide-y divide-bronze-faint">
          {filtered.map((item, i) => {
            const meta = KIND_META[item.kind];
            const Icon = meta.icon;
            return (
              <li
                key={item.id}
                className="relative flex items-start gap-3 px-5 py-4 hover:bg-obsidian-deep/40 transition-colors"
                style={{ animationDelay: `${i * 30}ms` }}
              >
                {/* timeline rail dot */}
                <div className="relative flex flex-col items-center">
                  <div className={cn("flex h-9 w-9 items-center justify-center rounded-lg ring-1", meta.bg, meta.ring)}>
                    <Icon className={cn("h-4 w-4", meta.color)} />
                  </div>
                  {i < filtered.length - 1 && (
                    <span className="absolute top-9 w-px h-[calc(100%-1rem)] bg-bronze-faint" />
                  )}
                </div>
                <div className="min-w-0 flex-1 pt-0.5">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-semibold text-bronze-bright text-sm">
                      {item.agent}
                    </span>
                    <span className="text-[10px] px-1.5 py-0.5 rounded border border-bronze-faint text-titane/60 uppercase tracking-wide">
                      {item.dept}
                    </span>
                    <span className={cn("text-[10px] uppercase tracking-wide", meta.color)}>
                      {meta.label}
                    </span>
                  </div>
                  <p className="text-sm text-ivoire/85 leading-snug">
                    {item.action}
                  </p>
                  <span className="text-[10px] text-titane/40 mt-1 inline-flex items-center gap-1">
                    <ActivityIcon className="h-2.5 w-2.5" />
                    {item.time}
                  </span>
                </div>
              </li>
            );
          })}
        </ul>
      </div>
    </div>
  );
}
