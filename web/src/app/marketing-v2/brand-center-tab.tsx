"use client";

import { useEffect, useState } from "react";
import { C } from "../app-v2/shared";
import {
  fetchDesignSystem,
  reviewBrandText,
  type BrandDesignSystem,
  type BrandReviewResult,
} from "@/lib/brand-system-api";

export function BrandCenterTab() {
  const [ds, setDs] = useState<BrandDesignSystem | null>(null);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [review, setReview] = useState<BrandReviewResult | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    fetchDesignSystem()
      .then((data) => {
        if (!cancelled) setDs(data);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setLoadErr(err instanceof Error ? err.message : "Chargement impossible");
        }
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function onReview() {
    setBusy(true);
    setReview(null);
    try {
      const result = await reviewBrandText({
        text: draft,
        department: "marketing",
        sector: "company",
      });
      setReview(result);
    } catch (err: unknown) {
      setReview({
        ok: false,
        reviewer: "brand",
        flags: [err instanceof Error ? err.message : "erreur"],
        voice_ok: false,
        department: "marketing",
        sector: "company",
        preview: "",
        recommendation: "revise",
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-4 overflow-auto p-1">
      <header className="space-y-1">
        <h2 className="text-[15px] font-semibold" style={{ color: C.ivory }}>
          Brand Center
        </h2>
        <p className="max-w-2xl text-[11.5px] leading-relaxed" style={{ color: C.muted }}>
          Design system transversal (Phase 35) — tokens + voix Anouk, review de cohérence
          avant publication. Pas de débat LLM ici : flags structurels uniquement.
        </p>
      </header>

      {loadErr ? (
        <p className="text-[12px]" style={{ color: C.copperLight }}>
          {loadErr}
        </p>
      ) : null}

      <section className="grid gap-3 md:grid-cols-2">
        <div
          className="rounded-2xl border p-4"
          style={{ borderColor: C.line, background: "rgba(19,19,22,.45)" }}
        >
          <h3 className="mb-3 text-[12px] font-medium uppercase tracking-wide" style={{ color: C.warm }}>
            Couleurs
          </h3>
          <div className="flex flex-wrap gap-2">
            {(ds?.color_tokens ?? []).map((t) => (
              <div key={`${t.token}-${t.hex}`} className="flex items-center gap-2 text-[11px]">
                <span
                  className="h-7 w-7 rounded-md border"
                  style={{ background: t.hex, borderColor: C.line }}
                  title={t.hex}
                />
                <span style={{ color: C.ivory }}>
                  {t.token}
                  <span className="ml-1" style={{ color: C.muted }}>
                    {t.hex}
                  </span>
                </span>
              </div>
            ))}
            {!ds ? <span style={{ color: C.muted }}>…</span> : null}
          </div>
          <p className="mt-3 text-[10.5px]" style={{ color: C.muted }}>
            Source : {ds?.source.colors ?? "—"}
            {ds?.source.kit_id ? ` · kit ${ds.source.kit_id.slice(0, 8)}` : ""}
          </p>
        </div>

        <div
          className="rounded-2xl border p-4"
          style={{ borderColor: C.line, background: "rgba(19,19,22,.45)" }}
        >
          <h3 className="mb-3 text-[12px] font-medium uppercase tracking-wide" style={{ color: C.warm }}>
            Voix & guidelines
          </h3>
          <ul className="space-y-1.5 text-[11.5px] leading-relaxed" style={{ color: C.ivory }}>
            {ds?.voice.tone ? <li>Ton : {ds.voice.tone}</li> : null}
            {ds?.voice.forbidden ? <li>Interdit : {ds.voice.forbidden}</li> : null}
            {(ds?.guidelines ?? []).slice(0, 3).map((g) => (
              <li key={g} style={{ color: C.muted }}>
                · {g}
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section
        className="rounded-2xl border p-4"
        style={{ borderColor: C.line, background: "rgba(19,19,22,.45)" }}
      >
        <h3 className="mb-2 text-[12px] font-medium uppercase tracking-wide" style={{ color: C.warm }}>
          Review cohérence
        </h3>
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          rows={5}
          placeholder="Colle un draft post / campagne…"
          className="w-full resize-y rounded-xl border bg-transparent px-3 py-2 text-[12px] outline-none"
          style={{ borderColor: C.line, color: C.ivory }}
        />
        <div className="mt-3 flex items-center gap-3">
          <button
            type="button"
            disabled={busy || draft.trim().length < 1}
            onClick={() => void onReview()}
            className="rounded-full border px-4 py-1.5 text-[11.5px] disabled:opacity-40"
            style={{
              borderColor: "rgba(192,138,114,.45)",
              color: C.copperLight,
              background: "rgba(192,138,114,.12)",
            }}
          >
            {busy ? "Review…" : "Lancer la review Brand"}
          </button>
          {review ? (
            <span
              className="text-[11.5px]"
              style={{ color: review.ok ? "#8FBF9A" : C.copperLight }}
            >
              {review.recommendation}
              {review.flags.length ? ` — ${review.flags.join(", ")}` : " — aucun flag"}
            </span>
          ) : null}
        </div>
      </section>
    </div>
  );
}
