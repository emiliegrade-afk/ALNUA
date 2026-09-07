"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { ACTIVITY_LABELS } from "@/components/lounge/lounge-constants";
import type { LoungeAgentCard } from "@/components/lounge/lounge-agents-strip";
import {
  fetchActiveLoungeSessions,
  fetchLoungeLeaderboard,
  fetchLoungeTeamLeaderboard,
  type LoungeLeaderboardEntry,
  type LoungeSession,
} from "@/lib/lounge-api";
import type { AgentStatus } from "@/lib/openroom-api";
import { ROUTES } from "@/lib/routes";

type Props = {
  agents: LoungeAgentCard[];
  statuses: Record<string, AgentStatus>;
  refreshKey?: number;
};

type BoardTab = "global" | "depts" | "amis";

function agentName(agents: LoungeAgentCard[], id: string): string {
  return agents.find((a) => a.id === id)?.name ?? id;
}

function sessionTitle(s: LoungeSession): string {
  const act = (s.activity || "puzzle") as keyof typeof ACTIVITY_LABELS;
  return (ACTIVITY_LABELS[act] ?? s.activity ?? "Session").toUpperCase();
}

/** Colonne droite maquette : activité en cours + classement à onglets. */
export function LoungeSidePanel({ agents, statuses, refreshKey = 0 }: Props) {
  const [board, setBoard] = useState<LoungeLeaderboardEntry[]>([]);
  const [teamBoard, setTeamBoard] = useState<
    { team_id: string; team_label: string; total_score: number; rank: number }[]
  >([]);
  const [sessions, setSessions] = useState<LoungeSession[]>([]);
  const [err, setErr] = useState<string | null>(null);
  const [tab, setTab] = useState<BoardTab>("global");

  const reload = useCallback(() => {
    void fetchLoungeLeaderboard()
      .then((rows) => {
        setBoard(Array.isArray(rows) ? rows.filter((r) => r.score > 0).slice(0, 5) : []);
        setErr(null);
      })
      .catch((e) => {
        setErr(e instanceof Error ? e.message : "Classement indisponible");
        setBoard([]);
      });
    void fetchLoungeTeamLeaderboard()
      .then((rows) => setTeamBoard(Array.isArray(rows) ? rows.slice(0, 5) : []))
      .catch(() => setTeamBoard([]));
    void fetchActiveLoungeSessions()
      .then((rows) => setSessions(Array.isArray(rows) ? rows.slice(0, 5) : []))
      .catch(() => setSessions([]));
  }, []);

  useEffect(() => {
    reload();
  }, [reload, refreshKey]);

  const liveFallback = agents
    .filter((a) => {
      const s = statuses[a.id]?.status;
      return s === "working" || s === "waiting";
    })
    .slice(0, 4);

  const tabs: { id: BoardTab; label: string }[] = [
    { id: "global", label: "Global" },
    { id: "depts", label: "Départements" },
    { id: "amis", label: "Amis" },
  ];

  return (
    <aside className="flex h-full w-full flex-col gap-4">
      <section className="flex min-h-0 flex-1 flex-col rounded-2xl border border-white/8 bg-obsidian-2/90 p-4">
        <h2 className="mb-4 text-[11px] font-medium uppercase tracking-[0.18em] text-copper/90">
          Activité en cours
        </h2>

        {sessions.length > 0 ? (
          <ul className="space-y-3">
            {sessions.map((s) => (
              <li key={s.id} className="flex items-start gap-2.5">
                <AgentAvatar
                  agentId={s.agent_id}
                  name={agentName(agents, s.agent_id)}
                  size={36}
                  ring
                />
                <div className="min-w-0 flex-1">
                  <div className="flex items-start justify-between gap-2">
                    <p className="truncate text-sm text-ivory">
                      {agentName(agents, s.agent_id)}
                    </p>
                    <span className="shrink-0 font-mono text-[10px] text-titanium/45">
                      LIVE
                    </span>
                  </div>
                  <p className="truncate text-[11px] font-medium uppercase tracking-[0.06em] text-copper">
                    {sessionTitle(s)}
                  </p>
                  <p className="truncate text-[10px] text-titanium/45">
                    {s.puzzle_title ?? "Challenge"}
                  </p>
                </div>
                <span className="shrink-0 rounded-md bg-copper/15 px-1.5 py-0.5 text-[9px] font-semibold uppercase tracking-wide text-copper">
                  En cours
                </span>
              </li>
            ))}
          </ul>
        ) : liveFallback.length > 0 ? (
          <ul className="space-y-3">
            {liveFallback.map((a) => (
              <li key={a.id} className="flex items-start gap-2.5">
                <AgentAvatar
                  agentId={a.id}
                  name={a.name}
                  size={36}
                  status={statuses[a.id]?.status}
                  ring
                />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm text-ivory">{a.name}</p>
                  <p className="truncate text-[11px] uppercase tracking-[0.06em] text-copper">
                    {statuses[a.id]?.currentTask ?? "EN SESSION"}
                  </p>
                </div>
                <span className="shrink-0 rounded-md bg-copper/15 px-1.5 py-0.5 text-[9px] font-semibold uppercase text-copper">
                  En cours
                </span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-xs leading-relaxed text-titanium/45">
            Aucune session — lance une activité pour alimenter le live.
          </p>
        )}

        <button
          type="button"
          className="mt-auto pt-4 text-left text-[11px] text-copper/80 hover:text-copper"
          onClick={reload}
        >
          Voir toutes les activités →
        </button>
      </section>

      <section className="rounded-2xl border border-white/8 bg-obsidian-2/90 p-4">
        <h2 className="mb-3 text-[11px] font-medium uppercase tracking-[0.18em] text-copper/90">
          Classement hebdomadaire
        </h2>
        <div className="mb-3 flex rounded-lg border border-white/8 bg-obsidian-deep/60 p-0.5">
          {tabs.map((t) => (
            <button
              key={t.id}
              type="button"
              onClick={() => setTab(t.id)}
              className={`flex-1 rounded-md px-2 py-1.5 text-[10px] uppercase tracking-[0.08em] transition ${
                tab === t.id
                  ? "bg-copper/20 text-copper"
                  : "text-titanium/50 hover:text-titanium/80"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {err ? (
          <p className="text-xs text-amber-200/90">{err}</p>
        ) : tab === "depts" ? (
          teamBoard.length === 0 ? (
            <p className="text-xs text-titanium/50">Pas encore de score équipe.</p>
          ) : (
            <ol className="space-y-2.5">
              {teamBoard.map((row) => (
                <li key={row.team_id} className="flex items-center gap-2">
                  <span className="w-5 text-[11px] text-copper">#{row.rank}</span>
                  <span className="min-w-0 flex-1 truncate text-xs text-ivory">
                    {row.team_label}
                  </span>
                  <span className="text-xs tabular-nums text-copper">
                    {row.total_score.toLocaleString("fr-FR")}
                  </span>
                </li>
              ))}
            </ol>
          )
        ) : board.length === 0 ? (
          <p className="text-xs text-titanium/50">
            Aucun XP ce mois — gagne un challenge.
          </p>
        ) : (
          <ol className="space-y-2.5">
            {board.map((row) => {
              const name =
                `${row.first_name} ${row.last_name}`.trim() || row.agent_id;
              const trophy =
                row.rank === 1 ? "🥇" : row.rank === 2 ? "🥈" : row.rank === 3 ? "🥉" : "🏅";
              return (
                <li key={row.agent_id} className="flex items-center gap-2">
                  <span className="w-4 text-center text-[11px]">{trophy}</span>
                  <AgentAvatar agentId={row.agent_id} name={name} size={28} ring />
                  <span className="min-w-0 flex-1 truncate text-xs text-ivory">
                    {name}
                  </span>
                  <span className="text-xs tabular-nums text-copper">
                    {row.score.toLocaleString("fr-FR")}
                  </span>
                </li>
              );
            })}
          </ol>
        )}

        <Link
          href={ROUTES.competition}
          className="mt-4 inline-block text-[11px] text-copper/75 hover:text-copper hover:underline"
        >
          Voir le classement complet →
        </Link>
      </section>
    </aside>
  );
}
