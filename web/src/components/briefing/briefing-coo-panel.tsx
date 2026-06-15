"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Loader2, Sparkles, Target } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { CooDailyBriefing } from "@/lib/briefing-api";

function RawCooAccordion({ data }: { data: CooDailyBriefing["raw_data"] }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="rounded-xl border border-white/10 bg-white/[0.02]">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between px-4 py-3 text-left text-sm text-titanium hover:text-ivory"
      >
        <span>Données agrégées (leaderboard, coûts, events)</span>
        {open ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>
      {open && (
        <pre className="max-h-80 overflow-auto border-t border-white/10 px-4 py-4 font-mono text-xs text-titanium/80">
          {JSON.stringify(data, null, 2)}
        </pre>
      )}
    </div>
  );
}

export function BriefingCooPanel({
  briefing,
  loading,
  onRefresh,
}: {
  briefing: CooDailyBriefing | null;
  loading: boolean;
  onRefresh: () => void;
}) {
  const coo = briefing?.coo_brief;
  const priorities = coo
    ? [coo.priority_1, coo.priority_2, coo.priority_3].filter(Boolean)
    : [];

  if (loading && !briefing) {
    return (
      <div className="flex flex-col items-center gap-3 py-20">
        <Loader2 className="h-8 w-8 animate-spin text-copper/60" />
        <p className="text-sm text-titanium">
          Aria synthétise le brief exécutif (trends, coûts, events)…
        </p>
      </div>
    );
  }

  if (!briefing || !coo) {
    return (
      <Card className="border-copper/20 bg-surface/60">
        <CardContent className="flex flex-col items-center gap-4 py-16 text-center">
          <Sparkles className="h-10 w-10 text-copper/60" />
          <p className="max-w-md text-sm text-titanium">
            Le brief exécutif COO agrège leaderboard, tendances, coûts LLM et
            events. Génère-le pour orienter ta journée.
          </p>
          <Button
            type="button"
            onClick={onRefresh}
            disabled={loading}
            className="bg-copper text-obsidian hover:bg-copper-glow"
          >
            {loading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : null}
            Générer brief COO
          </Button>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <Card className="border-copper/20 bg-surface/80">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-xl text-ivory">
            <Sparkles className="h-5 w-5 text-copper" />
            Brief exécutif — Aria (COO)
          </CardTitle>
          <p className="text-xs text-titanium/60">
            {briefing.date} · {briefing.duration_ms}ms
            {briefing.raw_data.trends_collected ? " · trends inclus" : ""}
          </p>
        </CardHeader>
        <CardContent className="space-y-6">
          {coo.headline && (
            <p className="text-lg font-medium leading-relaxed text-ivory">
              {coo.headline}
            </p>
          )}

          {priorities.length > 0 && (
            <section>
              <h3 className="mb-3 flex items-center gap-2 text-sm font-medium text-copper-glow">
                <Target className="h-4 w-4" />
                Priorités du jour
              </h3>
              <ol className="space-y-2">
                {priorities.map((p, i) => (
                  <li
                    key={`priority-${i}`}
                    className="rounded-lg border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-ivory/90"
                  >
                    <span className="mr-2 font-semibold text-copper">{i + 1}.</span>
                    {p}
                  </li>
                ))}
              </ol>
            </section>
          )}

          {(coo.alerts?.length ?? 0) > 0 && (
            <section>
              <h3 className="mb-2 text-sm font-medium text-red-400">Alertes</h3>
              <ul className="space-y-1.5 text-sm text-ivory/85">
                {coo.alerts!.map((a, i) => (
                  <li key={`alert-${i}`}>• {a}</li>
                ))}
              </ul>
            </section>
          )}

          {(coo.opportunities?.length ?? 0) > 0 && (
            <section>
              <h3 className="mb-2 text-sm font-medium text-emerald-400">
                Opportunités
              </h3>
              <ul className="space-y-1.5 text-sm text-ivory/85">
                {coo.opportunities!.map((o, i) => (
                  <li key={`opp-${i}`}>• {o}</li>
                ))}
              </ul>
            </section>
          )}

          {coo.team_performance && (
            <p className="text-sm text-titanium">
              <span className="text-copper-glow">Équipe :</span>{" "}
              {coo.team_performance}
            </p>
          )}

          {coo.recommended_focus && (
            <p className="rounded-lg border border-copper/20 bg-copper/5 px-4 py-3 text-sm text-ivory/90">
              <span className="font-medium text-copper-glow">Focus 80% :</span>{" "}
              {coo.recommended_focus}
            </p>
          )}
        </CardContent>
      </Card>

      <RawCooAccordion data={briefing.raw_data} />
    </div>
  );
}
