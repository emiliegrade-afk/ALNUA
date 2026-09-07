"use client";

import { useEffect, useState } from "react";
import { ConsoleProvider } from "@/components/console/console-provider";
import { DeptV2PageShell } from "@/components/dept-v2";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { SiegeLifeLinks } from "@/components/shared/siege-life-links";
import { C } from "@/app/app-v2/shared";
import {
  fetchLeaderboard,
  type LeaderboardEntry,
} from "@/lib/marketing-api";
import { ROUTES } from "@/lib/routes";
import Link from "next/link";

/** Classement compétition agents — visible depuis HQ / CEO / Direction. */
export default function CompetitionPage() {
  const [rows, setRows] = useState<LeaderboardEntry[]>([]);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    void fetchLeaderboard()
      .then((data) => setRows(Array.isArray(data) ? data : []))
      .catch((e) => setErr(e instanceof Error ? e.message : "Hub injoignable"));
  }, []);

  return (
    <ConsoleProvider>
      <DeptV2PageShell
        deptHref={ROUTES.competition}
        activeDeptId="hub"
        coreSubtitle="Compétition"
      >
        <div
          className="alnua-scroll flex min-w-0 flex-1 flex-col gap-4 overflow-y-auto px-4 pb-4 pt-3.5"
          style={{ color: C.ivory }}
        >
          <div>
            <h1 className="text-[23px] leading-[1.1] tracking-[1px]">
              <span className="font-bold">COMPÉTITION</span>{" "}
              <span className="font-light tracking-[4px]" style={{ color: C.titanium }}>
                AGENTS
              </span>
            </h1>
            <p className="mt-0.5 text-[11px]" style={{ color: C.dim }}>
              Points du mois · milestones · ≠ trust score
            </p>
          </div>
          <SiegeLifeLinks />
          {err ? (
            <p className="border border-amber-500/30 px-3 py-2 text-sm text-amber-200">{err}</p>
          ) : null}
          <ol className="space-y-2 border border-titanium/20 bg-transparent p-3">
            {rows.length === 0 && !err ? (
              <li className="text-sm text-titanium/60">Chargement du classement…</li>
            ) : null}
            {rows.map((row) => {
              const name = `${row.first_name} ${row.last_name}`.trim() || row.agent_id;
              return (
                <li
                  key={row.agent_id}
                  className="flex items-center gap-3 border-b border-titanium/10 py-2 last:border-0"
                >
                  <span className="w-8 text-sm text-copper">#{row.rank}</span>
                  <AgentAvatar agentId={row.agent_id} name={name} size={40} ring />
                  <span className="min-w-0 flex-1">
                    <span className="block text-sm text-ivory">{name}</span>
                    <span className="block text-[11px] text-titanium/55">
                      {row.team} · {row.milestone_status || "—"}
                    </span>
                  </span>
                  <span className="text-sm tabular-nums text-copper">{row.score} pts</span>
                </li>
              );
            })}
          </ol>
          <p className="text-[11px]" style={{ color: C.dim }}>
            Ambiance du siège →{" "}
            <Link href={ROUTES.lounge} className="text-copper hover:underline">
              Agent Lounge
            </Link>
          </p>
        </div>
      </DeptV2PageShell>
    </ConsoleProvider>
  );
}
