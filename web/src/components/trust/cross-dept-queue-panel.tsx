"use client";

import { useCallback, useEffect, useState } from "react";
import { GitBranch, Loader2, Play, Plus } from "lucide-react";
import { C } from "@/app/app-v2/shared";
import {
  drainCrossDeptQueue,
  emitCrossDeptProject,
  fetchCrossDeptQueue,
  type CrossDeptItem,
} from "@/lib/trust-api";

/** Phase 36 Depth+ — file inter-départements + drain exécutable. */
export function CrossDeptQueuePanel() {
  const [items, setItems] = useState<CrossDeptItem[]>([]);
  const [title, setTitle] = useState("");
  const [loading, setLoading] = useState(false);
  const [draining, setDraining] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      setItems(await fetchCrossDeptQueue(40));
    } catch (err) {
      setError(err instanceof Error ? err.message : "File inaccessible");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function onEmit() {
    if (!title.trim()) return;
    setDraining(true);
    setError(null);
    setNote(null);
    try {
      const res = await emitCrossDeptProject({ title: title.trim() });
      setNote(`Émis ${res.event_id ?? "ok"} — ${res.queued?.length ?? 0} en file`);
      setTitle("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Émission impossible");
    } finally {
      setDraining(false);
    }
  }

  async function onDrain() {
    setDraining(true);
    setError(null);
    setNote(null);
    try {
      const res = await drainCrossDeptQueue(3);
      setNote(
        `Drain : ${res.ok}/${res.processed} OK` +
          (res.llm_enabled === false ? " (squelettes, LLM off)" : ""),
      );
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Drain impossible");
    } finally {
      setDraining(false);
    }
  }

  const queued = items.filter((i) => i.status === "queued").length;

  return (
    <section
      className="rounded-[12px] border p-4"
      style={{ borderColor: C.line, background: "rgba(0,0,0,0.22)" }}
    >
      <div className="mb-3 flex flex-wrap items-start justify-between gap-2">
        <div className="flex items-center gap-2">
          <GitBranch className="h-4 w-4" style={{ color: C.copper }} />
          <div>
            <h2 className="text-[13px] font-semibold tracking-wide" style={{ color: C.ivory }}>
              Cross-département
            </h2>
            <p className="text-[10px]" style={{ color: C.dim }}>
              Projet validé → Marketing / Finance / Analytics · {queued} en attente
            </p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => void onDrain()}
          disabled={draining || queued === 0}
          className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[11px] disabled:opacity-40"
          style={{ borderColor: C.copper, color: C.copperLight }}
        >
          {draining ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : <Play className="h-3.5 w-3.5" />}
          Drain ×3
        </button>
      </div>

      <div className="mb-3 flex flex-wrap gap-2">
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="Titre projet à valider…"
          className="min-w-[200px] flex-1 rounded-lg border bg-transparent px-2 py-1.5 text-[12px]"
          style={{ borderColor: C.line, color: C.ivory }}
        />
        <button
          type="button"
          onClick={() => void onEmit()}
          disabled={draining || !title.trim()}
          className="inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-[11px] disabled:opacity-40"
          style={{ borderColor: C.line, color: C.warm }}
        >
          <Plus className="h-3.5 w-3.5" />
          Émettre
        </button>
      </div>

      {error ? (
        <p className="mb-2 text-[11px]" style={{ color: "#f87171" }}>
          {error}
        </p>
      ) : null}
      {note ? (
        <p className="mb-2 text-[11px]" style={{ color: C.online }}>
          {note}
        </p>
      ) : null}

      {loading && items.length === 0 ? (
        <p className="text-[11px]" style={{ color: C.faint }}>
          Chargement…
        </p>
      ) : items.length === 0 ? (
        <p className="text-[11px]" style={{ color: C.faint }}>
          File vide — émets un projet ou valide via workflow.
        </p>
      ) : (
        <ul className="flex max-h-[240px] flex-col gap-1.5 overflow-y-auto">
          {items.slice(0, 20).map((item) => (
            <li
              key={item.id}
              className="flex items-center justify-between gap-2 rounded-lg border px-2.5 py-1.5 text-[11px]"
              style={{ borderColor: C.lineSoft }}
            >
              <span className="min-w-0 flex-1 truncate" style={{ color: C.ivory }}>
                <span style={{ color: C.copperLight }}>{item.department}</span>
                {" · "}
                {item.action}
                {item.title ? ` — ${item.title}` : ""}
              </span>
              <span
                className="shrink-0 uppercase"
                style={{
                  color:
                    item.status === "done"
                      ? C.online
                      : item.status === "failed"
                        ? "#f87171"
                        : C.faint,
                }}
              >
                {item.status}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
