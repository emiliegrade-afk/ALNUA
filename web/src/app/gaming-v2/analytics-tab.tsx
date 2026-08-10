"use client";

import { useEffect, useState } from "react";
import { fetchGamingCommunityStats } from "@/lib/gaming-community";
import type { GamingCommunityStats, Project } from "@/lib/types";
import { C } from "../app-v2/shared";
import { pct } from "./mock-data";

/* Analytics Gaming — PERFORMANCE MOTEUR et RENDU (Lumen/Nanite) restent des
 * valeurs de démonstration : aucune télémétrie de build/perf n'est branchée
 * (voir Phase 16, ROADMAP.md — pas de pipeline UE5 réel). COMMUNAUTÉ &
 * DISTRIBUTION est réel depuis la Phase 18 (ROADMAP.md, 2026-07-30) :
 * joueurs Steam simultanés + membres Discord via @/lib/gaming-community,
 * "—" tant que STEAM_APP_ID/DISCORD_BOT_TOKEN+DISCORD_GUILD_ID ne sont pas
 * configurés (.env). Steam Wishlist n'est volontairement pas affiché : Valve
 * n'expose pas ce chiffre via une API publique (accès Steamworks Partner
 * requis) — voir skills/skill_steam.py. Rétention D7/Playtests restent
 * provisoires, hors scope. */

function Tile({ label, value, unit, warn }: { label: string; value: number | string; unit?: string; warn?: boolean }) {
  return (
    <div className="rounded-xl border p-3 text-center" style={{ borderColor: C.line, background: "#000000" }}>
      <p className="text-[19px] font-semibold" style={{ color: warn ? "#f87171" : C.ivory }}>
        {value}
        {unit ? <span className="text-[11px]" style={{ color: C.faint }}>{unit}</span> : null}
      </p>
      <p className="text-[8.5px]" style={{ color: C.faint }}>
        {label}
      </p>
    </div>
  );
}

export function AnalyticsTab({ projects }: { projects: Project[] }) {
  const seed = projects[0]?.id ?? "gaming-default";
  const fps = pct(`${seed}-fps`, 45, 120);
  const ram = pct(`${seed}-ram`, 4, 12);
  const gpu = pct(`${seed}-gpu`, 40, 95);
  const buildMin = pct(`${seed}-buildtime`, 8, 45);
  const drawCalls = pct(`${seed}-draw`, 800, 4000);
  const triangles = pct(`${seed}-tri`, 2, 18);
  const retention = pct(`${seed}-retention`, 20, 65);
  const playtests = pct(`${seed}-playtests`, 3, 40);

  const [community, setCommunity] = useState<GamingCommunityStats | null>(null);
  useEffect(() => {
    let cancelled = false;
    fetchGamingCommunityStats().then((s) => {
      if (!cancelled) setCommunity(s);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto pb-2">
      <section>
        <p className="mb-2 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
          PERFORMANCE MOTEUR
        </p>
        <div className="grid grid-cols-3 gap-2.5 lg:grid-cols-6">
          <Tile label="FPS moyen" value={fps} warn={fps < 60} />
          <Tile label="RAM" value={ram} unit="Go" />
          <Tile label="GPU" value={gpu} unit="%" warn={gpu > 90} />
          <Tile label="Temps de build" value={buildMin} unit="min" />
          <Tile label="Draw calls" value={drawCalls} />
          <Tile label="Triangles" value={`${triangles}M`} />
        </div>
      </section>

      <section>
        <p className="mb-2 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
          RENDU (LUMEN / NANITE)
        </p>
        <div className="grid grid-cols-2 gap-2.5 lg:grid-cols-4">
          <Tile label="Lumen — coût GI" value={pct(`${seed}-lumen`, 2, 9)} unit="ms" />
          <Tile label="Nanite — clusters" value={`${pct(`${seed}-nanite`, 1, 8)}M`} />
          <Tile label="Packaging" value={pct(`${seed}-pkg`, 1, 5)} unit="Go" />
          <Tile label="Crashs (7j)" value={pct(`${seed}-crash7`, 0, 15)} warn={pct(`${seed}-crash7`, 0, 15) > 8} />
        </div>
      </section>

      <section>
        <p className="mb-2 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
          COMMUNAUTÉ &amp; DISTRIBUTION
        </p>
        <div className="grid grid-cols-2 gap-2.5 lg:grid-cols-4">
          <Tile
            label="Joueurs en ligne (Steam)"
            value={community?.steam_configured ? (community.steam_concurrent_players?.toLocaleString("fr-FR") ?? "—") : "Non configuré"}
          />
          <Tile
            label="Membres Discord"
            value={community?.discord_configured ? (community.discord_member_count?.toLocaleString("fr-FR") ?? "—") : "Non configuré"}
          />
          <Tile label="Rétention D7" value={retention} unit="%" />
          <Tile label="Playtests menés" value={playtests} />
        </div>
        <p className="mt-2 text-[8.5px]" style={{ color: C.faint }}>
          Steam Wishlist non affiché : non exposé par une API publique Valve (accès Steamworks Partner requis).
        </p>
      </section>
    </div>
  );
}
