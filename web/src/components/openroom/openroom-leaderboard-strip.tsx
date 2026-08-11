"use client";

import { useEffect, useState } from "react";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import {
  fetchLeaderboard,
  type LeaderboardEntry,
} from "@/lib/marketing-api";

/** Mini classement compétition — vie du siège (H5). */
export function OpenRoomLeaderboardStrip() {
  const [rows, setRows] = useState<LeaderboardEntry[]>([]);

  useEffect(() => {
    void fetchLeaderboard()
      .then((data) => setRows(Array.isArray(data) ? data.slice(0, 5) : []))
      .catch(() => setRows([]));
  }, []);

  if (rows.length === 0) return null;

  return (
    <div className="rounded-xl border border-copper/20 bg-obsidian-2 p-4">
      <h3 className="label-caps mb-3">Classement du mois</h3>
      <ul className="flex flex-wrap gap-3">
        {rows.map((row) => {
          const name = `${row.first_name} ${row.last_name}`.trim() || row.agent_id;
          return (
            <li
              key={row.agent_id}
              className="flex items-center gap-2 rounded-lg border border-copper/15 bg-obsidian-1 px-2.5 py-1.5"
            >
              <span className="text-[10px] text-copper/70">#{row.rank}</span>
              <AgentAvatar agentId={row.agent_id} name={name} size={28} />
              <span className="text-xs text-ivory">{row.first_name}</span>
              <span className="text-[11px] text-titanium/60">{row.score} pts</span>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
