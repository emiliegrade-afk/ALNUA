"use client";

import { useEffect, useState } from "react";
import {
  fetchLoungeTournaments,
  type LoungeTournament,
} from "@/lib/lounge-api";

const CTA: Record<string, string> = {
  "code-arena": "S'inscrire",
  "puzzle-master": "Jouer",
  "arcade-cup": "S'inscrire",
  "strategy-league": "Voir",
};

/** Footer maquette : événements + récompense du jour. */
export function LoungeEventsRow() {
  const [events, setEvents] = useState<LoungeTournament[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [claimed, setClaimed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    void fetchLoungeTournaments()
      .then((rows) => {
        if (!cancelled) {
          setEvents(rows.slice(0, 4));
          setError(null);
        }
      })
      .catch((e: unknown) => {
        if (!cancelled) {
          setError(e instanceof Error ? e.message : "Tournois indisponibles");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section>
      <h2 className="mb-3 text-[11px] font-medium uppercase tracking-[0.18em] text-copper/90">
        Événements & tournois
      </h2>
      {error ? (
        <p className="mb-2 text-xs text-amber-200/80">{error}</p>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        {events.map((ev) => (
          <article
            key={ev.id}
            className="flex flex-col rounded-2xl border border-white/8 bg-obsidian-2/80 p-3.5"
            style={
              ev.status === "live"
                ? { boxShadow: "0 0 24px rgba(224,155,106,0.12)" }
                : undefined
            }
          >
            <p className="text-sm font-medium text-ivory">{ev.title}</p>
            <p className="mt-1.5 flex-1 text-[11px] leading-snug text-titanium/55">
              {ev.detail}
            </p>
            <p className="mt-2 text-[10px] uppercase tracking-[0.12em] text-copper/80">
              {ev.when_label}
              {ev.reward_xp ? ` · +${ev.reward_xp}` : ""}
            </p>
            <button
              type="button"
              className="mt-3 rounded-lg border border-white/10 bg-obsidian-deep/70 py-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-ivory/85 transition hover:border-copper/45 hover:text-copper"
            >
              {CTA[ev.id] ?? "Voir"}
            </button>
          </article>
        ))}

        <article
          className="relative flex flex-col overflow-hidden rounded-2xl border border-copper/35 bg-obsidian-2/90 p-4 sm:col-span-2 lg:col-span-1"
          style={{ boxShadow: "0 0 36px rgba(224,155,106,0.14)" }}
        >
          <p className="text-center text-[11px] font-medium uppercase tracking-[0.18em] text-copper">
            Récompense du jour
          </p>
          <div className="mt-3 flex flex-1 flex-col items-center justify-center gap-2 text-center">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="/lounge/reward-chest.png"
              alt=""
              className="h-16 w-16 object-contain"
            />
            <p className="text-lg font-semibold text-copper">+ 200 POINTS</p>
            <p className="text-[11px] leading-snug text-titanium/60">
              Viens jouer pour réclamer ta récompense !
            </p>
          </div>
          <button
            type="button"
            disabled={claimed}
            onClick={() => setClaimed(true)}
            className="mt-4 w-full rounded-lg border border-copper/55 bg-copper/15 py-2.5 text-[11px] font-semibold uppercase tracking-[0.18em] text-copper transition hover:bg-copper/25 disabled:cursor-default disabled:opacity-50"
          >
            {claimed ? "Récupérée" : "Récupérer"}
          </button>
        </article>
      </div>
    </section>
  );
}
