"use client";

import { useEffect, useState } from "react";
import { fetchLoungeLeaderboard } from "@/lib/lounge-api";

/** Badge POINTS LOUNGE — diamant + total (maquette). */
export function LoungePointsBadge() {
  const [total, setTotal] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    void fetchLoungeLeaderboard()
      .then((rows) => {
        if (cancelled) return;
        const sum = Array.isArray(rows)
          ? rows.reduce((acc, r) => acc + (r.score || 0), 0)
          : 0;
        setTotal(sum);
      })
      .catch(() => {
        if (!cancelled) setTotal(null);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (total === null) return null;

  return (
    <div
      className="inline-flex items-center gap-2.5 rounded-xl border border-copper/40 bg-obsidian-deep/80 px-3.5 py-2"
      style={{ boxShadow: "0 0 24px rgba(224, 155, 106, 0.18)" }}
      title="XP Lounge du mois (≠ compétition métier)"
    >
      <span className="text-base text-copper" aria-hidden>
        ◆
      </span>
      <div className="leading-tight">
        <p className="text-sm font-semibold tabular-nums tracking-wide text-ivory">
          {total.toLocaleString("fr-FR")}
        </p>
        <p className="text-[9px] uppercase tracking-[0.16em] text-copper/80">
          Points Lounge
        </p>
      </div>
    </div>
  );
}
