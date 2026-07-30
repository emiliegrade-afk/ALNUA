"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchRoboLabTests } from "@/lib/robo-lab-tests";
import type { Project, RoboLabTest } from "@/lib/types";
import { C } from "../app-v2/shared";

/* Laboratoire — journal réel (Phase 19, ROADMAP.md, 2026-07-30), rapporté
 * via scripts/report_lab_test.py après un vrai essai sur banc. Catégories
 * dérivées dynamiquement des vraies données. Vide tant qu'aucun test n'a été
 * rapporté (aucun banc connecté aujourd'hui). */

const STATUS_LABEL: Record<string, string> = { pass: "Réussi", fail: "Échec", in_progress: "En cours" };
const STATUS_COLOR: Record<string, string> = { pass: C.online, fail: "#f87171", in_progress: C.copperLight };

function timeAgo(iso: string): string {
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
  if (days <= 0) return "aujourd'hui";
  if (days === 1) return "hier";
  return `il y a ${days} j`;
}

export function LaboratoireTab({ projects }: { projects: Project[] }) {
  const [entries, setEntries] = useState<RoboLabTest[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>("Tous");

  const projectId = projects[0]?.id;
  const projectName = projects[0]?.name ?? "Eve";

  useEffect(() => {
    if (!projectId) {
      setLoading(false);
      return;
    }
    let cancelled = false;
    fetchRoboLabTests(projectId)
      .then((e) => {
        if (!cancelled) setEntries(e);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const categories = useMemo(() => Array.from(new Set(entries.map((e) => e.category))).sort(), [entries]);
  const visible = filter === "Tous" ? entries : entries.filter((e) => e.category === filter);

  if (loading) {
    return (
      <div className="flex min-h-[220px] flex-1 items-center justify-center rounded-xl text-[11px]" style={{ border: `1px solid ${C.line}`, color: C.faint }}>
        Chargement du laboratoire…
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto pb-2">
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            LABORATOIRE — {projectName.toUpperCase()}
          </p>
          <p className="text-[10px]" style={{ color: C.dim }}>
            Journal réel — rapporté via scripts/report_lab_test.py
          </p>
        </div>
        <span className="rounded-full border px-2.5 py-1 text-[9.5px]" style={{ borderColor: C.line, color: C.warm }}>
          {entries.length} entrées
        </span>
      </div>

      {entries.length === 0 ? (
        <div className="flex min-h-[220px] flex-1 flex-col items-center justify-center gap-2 rounded-xl border text-center text-[11px]" style={{ borderColor: C.line, color: C.faint }}>
          <p>Aucun test rapporté pour le moment.</p>
          <p className="text-[9.5px]" style={{ color: C.dim }}>
            Lance <code>python scripts/report_lab_test.py --project &quot;{projectName}&quot; --category &quot;...&quot; --name &quot;...&quot; --status pass</code>
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
                  borderColor: filter === c ? C.copper : "rgba(200,127,78,.2)",
                  background: filter === c ? "rgba(200,127,78,.15)" : "transparent",
                  color: filter === c ? C.copperLight : C.warm,
                }}
              >
                {c}
              </button>
            ))}
          </div>

          <div className="grid grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-2.5">
            {visible.map((e) => (
              <div key={e.id} className="flex flex-col gap-1.5 rounded-xl border p-3" style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}>
                <div className="flex items-center justify-between gap-2">
                  <span className="rounded-full border px-1.5 py-px text-[8px]" style={{ borderColor: "rgba(200,127,78,.22)", color: C.faint }}>
                    {e.category}
                  </span>
                  <span className="rounded-full border px-1.5 py-px text-[8px]" style={{ borderColor: "rgba(200,127,78,.22)", color: STATUS_COLOR[e.status] }}>
                    {STATUS_LABEL[e.status]}
                  </span>
                </div>
                <p className="truncate text-[11.5px] font-medium" style={{ color: C.ivory }}>
                  {e.name}
                </p>
                <div className="flex items-center justify-between text-[9px]" style={{ color: C.faint }}>
                  <span>{e.measured_value ?? "—"}</span>
                  <span>{timeAgo(e.created_at)}</span>
                </div>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
