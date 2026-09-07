"use client";

import { useState } from "react";
import { Loader2, Scale } from "lucide-react";
import { C } from "@/app/app-v2/shared";
import {
  evaluateReviewBoard,
  type ReviewBoardResult,
} from "@/lib/trust-api";

const DEPARTMENTS = [
  "app",
  "gaming",
  "robo",
  "marketing",
  "brand",
  "content",
  "rd",
  "finances",
  "seo",
] as const;

/** Mini Review Board — POST /review-board/evaluate (Phase 32). */
export function ReviewBoardPanel() {
  const [department, setDepartment] = useState<string>("app");
  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");
  const [producer, setProducer] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ReviewBoardResult | null>(null);

  async function onEvaluate() {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await evaluateReviewBoard({
        department,
        title: title.trim(),
        body: body.trim(),
        producer_agent_id: producer.trim() || undefined,
        record_trust: false,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Évaluation impossible");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section
      className="rounded-[12px] border p-4"
      style={{ borderColor: C.line, background: "rgba(0,0,0,0.22)" }}
    >
      <div className="mb-3 flex items-center gap-2">
        <Scale className="h-4 w-4" style={{ color: C.copper }} />
        <div>
          <h2 className="text-[13px] font-semibold tracking-wide" style={{ color: C.ivory }}>
            Review Board
          </h2>
          <p className="text-[10px]" style={{ color: C.dim }}>
            Gate structurelle · trust non enregistré depuis cet essai
          </p>
        </div>
      </div>

      <div className="grid gap-2 sm:grid-cols-2">
        <label className="text-[10px] uppercase tracking-wider" style={{ color: C.dim }}>
          Département
          <select
            value={department}
            onChange={(e) => setDepartment(e.target.value)}
            className="mt-1 w-full rounded-lg border bg-transparent px-2 py-1.5 text-[12px]"
            style={{ borderColor: C.line, color: C.ivory }}
          >
            {DEPARTMENTS.map((d) => (
              <option key={d} value={d} style={{ color: "#111" }}>
                {d}
              </option>
            ))}
          </select>
        </label>
        <label className="text-[10px] uppercase tracking-wider" style={{ color: C.dim }}>
          Producteur (optionnel)
          <input
            value={producer}
            onChange={(e) => setProducer(e.target.value)}
            placeholder="ex. marketing"
            className="mt-1 w-full rounded-lg border bg-transparent px-2 py-1.5 text-[12px]"
            style={{ borderColor: C.line, color: C.ivory }}
          />
        </label>
      </div>

      <label className="mt-2 block text-[10px] uppercase tracking-wider" style={{ color: C.dim }}>
        Titre
        <input
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          className="mt-1 w-full rounded-lg border bg-transparent px-2 py-1.5 text-[12px]"
          style={{ borderColor: C.line, color: C.ivory }}
        />
      </label>

      <label className="mt-2 block text-[10px] uppercase tracking-wider" style={{ color: C.dim }}>
        Corps (≥ 40 car. pour score)
        <textarea
          value={body}
          onChange={(e) => setBody(e.target.value)}
          rows={4}
          className="mt-1 w-full rounded-lg border bg-transparent px-2 py-1.5 text-[12px]"
          style={{ borderColor: C.line, color: C.ivory }}
        />
      </label>

      <button
        type="button"
        disabled={loading || title.trim().length < 3 || body.trim().length < 10}
        onClick={() => void onEvaluate()}
        className="mt-3 inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-[11px] font-semibold uppercase tracking-[0.14em] disabled:opacity-40"
        style={{ borderColor: `${C.copper}88`, color: C.copper, background: "rgba(224,155,106,0.12)" }}
      >
        {loading ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
        Évaluer
      </button>

      {error ? (
        <p className="mt-2 text-[11px]" style={{ color: "#e8a090" }}>
          {error}
        </p>
      ) : null}

      {result ? (
        <div
          className="mt-3 rounded-lg border px-3 py-2.5 text-[12px]"
          style={{ borderColor: C.line, background: "rgba(255,255,255,0.03)" }}
        >
          <p style={{ color: C.ivory }}>
            {result.gate_open ? "Gate ouverte" : "Gate fermée"} · score{" "}
            <span className="tabular-nums" style={{ color: C.copper }}>
              {Math.round(result.score)}
            </span>
            /{Math.round(result.threshold)} · {result.recommendation ?? "—"}
          </p>
          {result.checks && result.checks.length > 0 ? (
            <ul className="mt-2 space-y-1 text-[10px]" style={{ color: C.dim }}>
              {result.checks.map((c) => (
                <li key={c.id}>
                  {c.ok ? "✓" : "✗"} {c.id}
                  {c.error ? ` — ${c.error}` : ""}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
