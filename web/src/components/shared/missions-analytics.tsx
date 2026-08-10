"use client";

import { useMemo } from "react";
import { Bars, Donut } from "@/components/console/charts";
import {
  PRIORITY_STYLES,
  TYPE_STYLES,
  type TicketPriority,
  type TicketType,
} from "@/components/tickets/tickets.constants";
import type { TicketWithProject } from "@/lib/tickets";

interface MissionsAnalyticsProps {
  tickets: TicketWithProject[];
}

const WEEK_MS = 7 * 24 * 60 * 60 * 1000;
const WEEKS = 6;

const TYPE_ORDER: TicketType[] = ["bug", "feature", "improvement", "crash"];
const PRIORITY_ORDER: TicketPriority[] = ["critical", "high", "medium", "low"];

const STATUS_DONUT = [
  { key: "open", label: "Backlog", color: "#E09B6A" },
  { key: "in_progress", label: "En cours", color: "#60a5fa" },
  { key: "in_review", label: "En revue", color: "#ffa500" },
  { key: "done", label: "Terminé", color: "#34d399" },
] as const;

/**
 * Panneau analytique sous le board Missions (maquette « Project Analytics »).
 * Tout est dérivé des tickets réellement chargés — la vélocité s'appuie sur
 * `updated_at` des tickets résolus, seule date de clôture dont le modèle
 * dispose ; le libellé le dit explicitement plutôt que de faire passer une
 * approximation pour une date de livraison.
 */
export function MissionsAnalytics({ tickets }: MissionsAnalyticsProps) {
  const stats = useMemo(() => {
    const counts = STATUS_DONUT.map((s) => ({
      ...s,
      value: tickets.filter((t) => t.status === s.key).length,
    }));

    const byType = TYPE_ORDER.map((type) => ({
      label: TYPE_STYLES[type].label,
      value: tickets.filter((t) => t.type === type).length,
    })).filter((d) => d.value > 0);

    const byPriority = PRIORITY_ORDER.map((priority) => ({
      label: PRIORITY_STYLES[priority].label,
      value: tickets.filter((t) => t.priority === priority).length,
    })).filter((d) => d.value > 0);

    // Vélocité : tickets résolus par tranche de 7 jours, la plus récente à droite.
    const now = Date.now();
    const velocity = Array.from({ length: WEEKS }, (_, i) => {
      const end = now - (WEEKS - 1 - i) * WEEK_MS;
      const start = end - WEEK_MS;
      const value = tickets.filter((t) => {
        if (t.status !== "done") return false;
        const ts = Date.parse(t.updated_at);
        return Number.isFinite(ts) && ts > start && ts <= end;
      }).length;
      return { label: i === WEEKS - 1 ? "S0" : `S-${WEEKS - 1 - i}`, value };
    });

    return { counts, byType, byPriority, velocity, total: tickets.length };
  }, [tickets]);

  if (stats.total === 0) return null;

  const active = stats.counts
    .filter((c) => c.key === "open" || c.key === "in_progress" || c.key === "in_review")
    .reduce((s, c) => s + c.value, 0);
  const done = stats.counts.find((c) => c.key === "done")?.value ?? 0;

  return (
    <section className="rounded-xl border border-bronze-faint bg-obsidian/70 p-4">
      <div className="mb-4 flex items-baseline justify-between gap-3">
        <h3 className="label-caps">Analytique des missions</h3>
        <span className="text-[10px] text-titane/40">{stats.total} tickets suivis</span>
      </div>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,220px)_1fr_1fr]">
        <div>
          <p className="mb-3 text-[10px] uppercase tracking-wide text-titane/50">
            Répartition du pipeline
          </p>
          <div className="flex items-center gap-4">
            <Donut
              segments={stats.counts
                .filter((c) => c.value > 0)
                .map((c) => ({ value: c.value, color: c.color }))}
              size={92}
              thickness={11}
              centerValue={String(stats.total)}
              centerLabel="missions"
            />
            <ul className="space-y-1.5 text-xs">
              {stats.counts.map((c) => (
                <li key={c.key} className="flex items-center gap-2">
                  <span
                    className="h-2 w-2 shrink-0 rounded-full"
                    style={{ background: c.color }}
                  />
                  <span className="text-titane/70">{c.label}</span>
                  <span className="ml-auto tabular-nums text-ivoire/80">{c.value}</span>
                </li>
              ))}
            </ul>
          </div>
          <div className="mt-3 grid grid-cols-2 gap-2 border-t border-bronze-faint pt-3 text-center">
            <div>
              <p className="text-lg font-bold text-gradient-bronze tabular-nums">{active}</p>
              <p className="text-[9px] uppercase tracking-wide text-titane/50">En cours</p>
            </div>
            <div>
              <p className="text-lg font-bold text-ivoire tabular-nums">{done}</p>
              <p className="text-[9px] uppercase tracking-wide text-titane/50">Terminées</p>
            </div>
          </div>
        </div>

        <div>
          <p className="mb-1 text-[10px] uppercase tracking-wide text-titane/50">Vélocité</p>
          <p className="mb-3 text-[9px] text-titane/35">
            Missions résolues par semaine (d&apos;après leur dernière mise à jour)
          </p>
          <Bars data={stats.velocity} height={128} color="#E09B6A" />
        </div>

        <div className="space-y-4">
          {stats.byType.length > 0 ? (
            <div>
              <p className="mb-2 text-[10px] uppercase tracking-wide text-titane/50">
                Par nature
              </p>
              <Bars data={stats.byType} height={92} color="#F0C4A0" />
            </div>
          ) : null}
          {stats.byPriority.length > 0 ? (
            <div>
              <p className="mb-2 text-[10px] uppercase tracking-wide text-titane/50">
                Par priorité
              </p>
              <Bars data={stats.byPriority} height={92} color="#A7ADB5" />
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
