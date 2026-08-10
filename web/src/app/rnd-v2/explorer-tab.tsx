"use client";

import { useEffect, useState } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { injectRndIdea } from "@/lib/rnd";
import {
  fetchExplorerBrief,
  fetchExplorerSignals,
  type ExplorerBriefResponse,
  type ExplorerSignal,
} from "@/lib/rnd-explorer-api";
import { C } from "../app-v2/shared";

const TOPIC_PRESETS = ["AI agents", "robotics", "Unreal Engine", "LLM", "edge AI"] as const;

export function ExplorerTab() {
  const [topics, setTopics] = useState<string[]>([...TOPIC_PRESETS]);
  const [customTopic, setCustomTopic] = useState("");
  const [items, setItems] = useState<ExplorerSignal[]>([]);
  const [emptyReason, setEmptyReason] = useState<string | null>(null);
  const [fetchedAt, setFetchedAt] = useState<string | null>(null);
  const [loadErr, setLoadErr] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [briefing, setBriefing] = useState(false);
  const [brief, setBrief] = useState<ExplorerBriefResponse | null>(null);
  const [seeding, setSeeding] = useState<string | null>(null);

  async function scan() {
    setScanning(true);
    setLoadErr(null);
    try {
      const res = await fetchExplorerSignals({ topics, limit: 40 });
      setItems(res.items);
      setEmptyReason(res.empty_reason);
      setFetchedAt(res.fetched_at);
    } catch (err: unknown) {
      setLoadErr(err instanceof Error ? err.message : "Scan impossible");
      setItems([]);
    } finally {
      setScanning(false);
    }
  }

  useEffect(() => {
    void scan();
    // Initial load only — manual refresh / topic change via buttons.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function toggleTopic(t: string) {
    setTopics((prev) => (prev.includes(t) ? prev.filter((x) => x !== t) : [...prev, t]));
  }

  function addCustom() {
    const t = customTopic.trim();
    if (!t || topics.includes(t)) return;
    setTopics((prev) => [...prev, t].slice(0, 12));
    setCustomTopic("");
  }

  async function runBrief() {
    setBriefing(true);
    try {
      const res = await fetchExplorerBrief({
        topics,
        agent_id: "brainstorm",
        limit: 25,
      });
      setBrief(res);
      if (!res.ok) toast.message(res.error || "Brief vide");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Brief échoué");
    } finally {
      setBriefing(false);
    }
  }

  async function seedIdea(title: string) {
    setSeeding(title);
    try {
      await injectRndIdea(`Veille Explorer : ${title}`);
      toast.success("Idée injectée dans le Pipeline");
    } catch (err: unknown) {
      toast.error(err instanceof Error ? err.message : "Injection échouée");
    } finally {
      setSeeding(null);
    }
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-auto p-1">
      <header className="space-y-1">
        <h2 className="text-[15px] font-semibold" style={{ color: C.ivory }}>
          Explorer — veille externe
        </h2>
        <p className="max-w-2xl text-[11.5px] leading-relaxed" style={{ color: C.muted }}>
          Signaux HN / Reddit / GitHub (réels). Brief Idris optionnel. Aucune métrique
          inventée si les sources sont down.
        </p>
      </header>

      <div className="flex flex-wrap items-center gap-2">
        {TOPIC_PRESETS.map((t) => {
          const on = topics.includes(t);
          return (
            <button
              key={t}
              type="button"
              onClick={() => toggleTopic(t)}
              className="rounded-full border px-2.5 py-1 text-[10.5px]"
              style={{
                borderColor: on ? "rgba(224,155,106,.5)" : C.line,
                color: on ? C.copperLight : C.muted,
                background: on ? "rgba(224,155,106,.12)" : "transparent",
              }}
            >
              {t}
            </button>
          );
        })}
        <input
          value={customTopic}
          onChange={(e) => setCustomTopic(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && addCustom()}
          placeholder="+ topic"
          className="w-28 rounded-full border bg-transparent px-2.5 py-1 text-[10.5px] outline-none"
          style={{ borderColor: C.line, color: C.ivory }}
        />
        <button
          type="button"
          disabled={scanning}
          onClick={() => void scan()}
          className="flex items-center gap-1.5 rounded-full border px-3 py-1 text-[10.5px] disabled:opacity-40"
          style={{ borderColor: "rgba(224,155,106,.4)", color: C.copperLight }}
        >
          {scanning ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
          Scanner
        </button>
        <button
          type="button"
          disabled={briefing}
          onClick={() => void runBrief()}
          className="flex items-center gap-1.5 rounded-full border px-3 py-1 text-[10.5px] disabled:opacity-40"
          style={{
            borderColor: "rgba(224,155,106,.4)",
            color: C.ivory,
            background: "rgba(224,155,106,.1)",
          }}
        >
          {briefing ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
          Brief Idris
        </button>
        {fetchedAt ? (
          <span className="text-[10px]" style={{ color: C.faint }}>
            {new Date(fetchedAt).toLocaleTimeString()}
          </span>
        ) : null}
      </div>

      {loadErr ? (
        <p className="text-[12px]" style={{ color: C.copperLight }}>
          {loadErr}
        </p>
      ) : null}

      {brief?.ok ? (
        <section
          className="rounded-2xl border p-4"
          style={{ borderColor: C.line, background: "rgba(19,22,27,.5)" }}
        >
          <p className="text-[10px] uppercase tracking-wider" style={{ color: C.faint }}>
            Synthèse labo
          </p>
          <p className="mt-1.5 text-[12px] leading-relaxed" style={{ color: C.ivory }}>
            {brief.synthesis}
          </p>
          {brief.dossier_hooks.length > 0 ? (
            <ul className="mt-3 space-y-1 text-[11px]" style={{ color: C.muted }}>
              {brief.dossier_hooks.map((h) => (
                <li key={h}>· {h}</li>
              ))}
            </ul>
          ) : null}
        </section>
      ) : null}

      <section className="flex flex-col gap-2">
        {items.length === 0 && !scanning ? (
          <p className="rounded-2xl border p-6 text-center text-[12px]" style={{ borderColor: C.line, color: C.muted }}>
            {emptyReason || "Aucun signal pour ces topics."}
          </p>
        ) : (
          items.map((item) => (
            <article
              key={`${item.source}-${item.url}-${item.title}`}
              className="flex flex-wrap items-start justify-between gap-2 rounded-xl border px-3 py-2.5"
              style={{ borderColor: C.line, background: "#000000" }}
            >
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2 text-[9.5px]" style={{ color: C.faint }}>
                  <span className="uppercase">{item.source}</span>
                  <span>score {item.score}</span>
                </div>
                <a
                  href={item.url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-0.5 block text-[12px] leading-snug hover:underline"
                  style={{ color: C.ivory }}
                >
                  {item.title}
                </a>
              </div>
              <button
                type="button"
                disabled={seeding === item.title}
                onClick={() => void seedIdea(item.title)}
                className="shrink-0 rounded-full border px-2.5 py-1 text-[10px] disabled:opacity-40"
                style={{ borderColor: "rgba(224,155,106,.35)", color: C.copperLight }}
              >
                → Pipeline
              </button>
            </article>
          ))
        )}
      </section>
    </div>
  );
}
