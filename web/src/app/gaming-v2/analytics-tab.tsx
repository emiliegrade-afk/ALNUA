"use client";

import { useEffect, useState } from "react";
import { fetchLatestGamingBuild } from "@/lib/gaming-builds";
import { fetchGamingCommunityStats } from "@/lib/gaming-community";
import type { GamingBuild, GamingCommunityStats, Project } from "@/lib/types";
import { C } from "../app-v2/shared";

/* Analytics Gaming — 100 % Hub-side :
 * - FPS / crashs / draw_calls = dernier build rapporté (gaming_builds)
 * - Steam / Discord = community-stats
 * - Métriques non instrumentées = « — » (plus de pct() / Démo)
 */

function Tile({
  label,
  value,
  unit,
  warn,
  empty,
}: {
  label: string;
  value: number | string;
  unit?: string;
  warn?: boolean;
  empty?: boolean;
}) {
  return (
    <div
      className="relative rounded-xl border p-3 text-center"
      style={{
        borderColor: empty ? `${C.line}` : C.line,
        background: "#000000",
        opacity: empty ? 0.75 : 1,
      }}
    >
      {empty ? (
        <span
          className="absolute right-1.5 top-1.5 rounded px-1 py-0.5 text-[7px] font-bold uppercase tracking-wider"
          style={{ color: C.faint, background: "rgba(255,255,255,0.04)" }}
        >
          N/A
        </span>
      ) : null}
      <p className="text-[19px] font-semibold" style={{ color: warn ? "#f87171" : C.ivory }}>
        {value}
        {unit && value !== "—" ? (
          <span className="text-[11px]" style={{ color: C.faint }}>
            {unit}
          </span>
        ) : null}
      </p>
      <p className="text-[8.5px]" style={{ color: C.faint }}>
        {label}
      </p>
    </div>
  );
}

function dash(n: number | null | undefined): string | number {
  return n == null ? "—" : n;
}

export function AnalyticsTab({ projects }: { projects: Project[] }) {
  const projectId = projects[0]?.id;
  const [build, setBuild] = useState<GamingBuild | null>(null);
  const [community, setCommunity] = useState<GamingCommunityStats | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    void Promise.all([
      projectId ? fetchLatestGamingBuild(projectId) : Promise.resolve(null),
      fetchGamingCommunityStats(),
    ]).then(([b, c]) => {
      if (cancelled) return;
      setBuild(b);
      setCommunity(c);
      setLoaded(true);
    });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const fps = build?.fps_avg ?? null;
  const crashes = build?.crashes ?? null;
  const drawCalls = build?.draw_calls ?? null;

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-y-auto pb-2">
      <section>
        <p className="mb-2 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
          PERFORMANCE MOTEUR
          {loaded && !build ? (
            <span className="ml-2" style={{ color: C.dim }}>
              · aucun build rapporté
            </span>
          ) : null}
        </p>
        <div className="grid grid-cols-3 gap-2.5 lg:grid-cols-6">
          <Tile
            label="FPS moyen"
            value={dash(fps)}
            warn={fps != null && fps < 60}
            empty={fps == null}
          />
          <Tile label="RAM" value="—" empty />
          <Tile label="GPU" value="—" empty />
          <Tile label="Temps de build" value="—" empty />
          <Tile label="Draw calls" value={dash(drawCalls)} empty={drawCalls == null} />
          <Tile label="Triangles" value="—" empty />
        </div>
      </section>

      <section>
        <p className="mb-2 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
          STABILITÉ &amp; BUILD
        </p>
        <div className="grid grid-cols-2 gap-2.5 lg:grid-cols-4">
          <Tile
            label="Crashs (dernier build)"
            value={dash(crashes)}
            warn={crashes != null && crashes > 5}
            empty={crashes == null}
          />
          <Tile
            label="Build #"
            value={build ? `#${build.build_number}` : "—"}
            empty={!build}
          />
          <Tile
            label="Moteur"
            value={build?.engine_version ?? "—"}
            empty={!build?.engine_version}
          />
          <Tile
            label="Branche"
            value={build?.branch ?? "—"}
            empty={!build?.branch}
          />
        </div>
        <p className="mt-2 text-[8.5px]" style={{ color: C.faint }}>
          Lumen / Nanite / packaging : non instrumentés — pas de chiffres inventés.
        </p>
      </section>

      <section>
        <p className="mb-2 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
          COMMUNAUTÉ &amp; DISTRIBUTION
        </p>
        <div className="grid grid-cols-2 gap-2.5 lg:grid-cols-4">
          <Tile
            label="Joueurs en ligne (Steam)"
            value={
              community?.steam_configured
                ? (community.steam_concurrent_players?.toLocaleString("fr-FR") ?? "—")
                : "Non configuré"
            }
            empty={!community?.steam_configured}
          />
          <Tile
            label="Membres Discord"
            value={
              community?.discord_configured
                ? (community.discord_member_count?.toLocaleString("fr-FR") ?? "—")
                : "Non configuré"
            }
            empty={!community?.discord_configured}
          />
          <Tile label="Rétention D7" value="—" empty />
          <Tile label="Playtests menés" value="—" empty />
        </div>
        <p className="mt-2 text-[8.5px]" style={{ color: C.faint }}>
          Steam Wishlist : non exposé par l&apos;API publique Valve (Steamworks Partner
          requis).
        </p>
      </section>
    </div>
  );
}
