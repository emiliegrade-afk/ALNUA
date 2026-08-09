"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchGamingAssets } from "@/lib/gaming-assets";
import type { GamingAsset, Project } from "@/lib/types";
import { C } from "../app-v2/shared";

/* Assets — inventaire réel (Phase 17, ROADMAP.md, 2026-07-30), synchronisé
 * via scripts/sync_ue5_assets.py depuis un dossier réel (le projet Wyrdheim
 * est sur un disque séparé, non accessible depuis le Hub). Catégories et
 * types dérivés du vrai scan (nom de dossier, extension) — pas de liste
 * fictive. Vide tant qu'aucune synchronisation n'a été lancée. */

const TYPE_ICON: Record<string, string> = {
  Texture: "🧱",
  Son: "🔊",
  Mesh: "🗿",
  Blueprint: "⚙",
  Niveau: "🗺",
  Animation: "🎞",
  Autre: "📄",
};

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} o`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} Ko`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} Mo`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} Go`;
}

function timeAgo(iso: string | null): string {
  if (!iso) return "—";
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
  if (days <= 0) return "aujourd'hui";
  if (days === 1) return "hier";
  return `il y a ${days} j`;
}

export function AssetsTab({ projects }: { projects: Project[] }) {
  const [assets, setAssets] = useState<GamingAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("Tous");

  const projectId = projects[0]?.id;
  const projectName = projects[0]?.name ?? "Wyrdheim Online";

  useEffect(() => {
    if (!projectId) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    fetchGamingAssets(projectId)
      .then((a) => {
        if (!cancelled) setAssets(a);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const categories = useMemo(() => Array.from(new Set(assets.map((a) => a.category))).sort(), [assets]);
  const visible = filter === "Tous" ? assets : assets.filter((a) => a.category === filter);

  if (loading) {
    return (
      <div className="flex min-h-[220px] flex-1 items-center justify-center rounded-xl text-[11px]" style={{ border: `1px solid ${C.line}`, color: C.faint }}>
        Chargement des assets…
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto pb-2">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            ASSETS — {projectName.toUpperCase()}
          </p>
          <p className="text-[10px]" style={{ color: C.dim }}>
            Inventaire réel — synchronisé via scripts/sync_ue5_assets.py
          </p>
        </div>
        <span className="rounded-full border px-2.5 py-1 text-[9.5px]" style={{ borderColor: C.line, color: C.warm }}>
          {assets.length} assets
        </span>
      </div>

      {assets.length === 0 ? (
        <div className="flex min-h-[220px] flex-1 flex-col items-center justify-center gap-2 rounded-xl border text-center text-[11px]" style={{ borderColor: C.line, color: C.faint }}>
          <p>Aucun asset synchronisé pour le moment.</p>
          <p className="text-[9.5px]" style={{ color: C.dim }}>
            Lance <code>python scripts/sync_ue5_assets.py --project &quot;{projectName}&quot; --root &lt;dossier Content&gt;</code>
          </p>
        </div>
      ) : (
        <>
          <div className="flex gap-2 overflow-x-auto">
            {(["Tous", ...categories] as const).map((c) => (
              <button
                key={c}
                type="button"
                onClick={() => setFilter(c)}
                className="shrink-0 rounded-full border px-3 py-1 text-[10px]"
                style={{
                  borderColor: filter === c ? C.copper : "rgba(192,138,114,.2)",
                  background: filter === c ? "rgba(192,138,114,.15)" : "transparent",
                  color: filter === c ? C.copperLight : C.warm,
                }}
              >
                {c}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-2.5">
            {visible.map((a) => (
              <div key={a.id} className="flex flex-col gap-1.5 rounded-xl border p-3" style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}>
                <div className="flex items-center justify-between gap-2">
                  <span className="text-[11px]">{TYPE_ICON[a.asset_type] ?? TYPE_ICON.Autre}</span>
                  <span className="rounded-full border px-1.5 py-px text-[8px]" style={{ borderColor: "rgba(192,138,114,.22)", color: C.faint }}>
                    {a.category}
                  </span>
                </div>
                <p className="truncate text-[11.5px] font-medium" style={{ color: C.ivory }}>
                  {a.name}
                </p>
                <div className="flex items-center justify-between text-[9px]" style={{ color: C.faint }}>
                  <span>{formatBytes(a.size_bytes)}</span>
                  <span>{timeAgo(a.modified_at)}</span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
