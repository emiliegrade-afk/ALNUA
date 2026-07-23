"use client";

import { useState } from "react";
import { BookOpen, ChevronDown, ChevronUp } from "lucide-react";
import { cn } from "@/lib/utils";

const AGENT_RECS: { agent: string; auto: string; force?: string }[] = [
  { agent: "COO", auto: "Sonnet 4", force: "Opus 4.8 ou Fable 5" },
  { agent: "Spec", auto: "Sonnet 4", force: "Sonnet 4.6 ou GPT-5.3 Codex" },
  { agent: "Brainstorm", auto: "Sonnet 4", force: "Grok 3 ou GLM 4.6" },
  { agent: "R&D", auto: "Sonnet 4", force: "Opus 4.8 ou GPT-5.5 Pro" },
  { agent: "Dev App / Gaming", auto: "DeepSeek V3.1", force: "Qwen3 Coder ou Sonnet 4.5" },
  { agent: "QA", auto: "DeepSeek V3.1", force: "GPT-4o Mini ou GLM 4.5 Air" },
  { agent: "Marketing / Content", auto: "DeepSeek V3.1", force: "Sonnet 4.5 ou Kimi K2.6" },
  { agent: "PM / Compta", auto: "Haiku 4.5", force: "Laisser en Auto" },
];

const TASK_RECS: { task: string; models: string; why: string }[] = [
  { task: "Stratégie & décisions", models: "Opus 4.8 · GPT-5.5 Pro · Kimi K2.6", why: "Raisonnement long, nuances" },
  { task: "Specs & prompts Cursor", models: "Sonnet 4.6 · GPT-5.3 Codex · DeepSeek V3.1", why: "Structuré, précis, markdown" },
  { task: "Code & fix de bugs", models: "Kimi K2.7 Code · GPT-5.3 Codex · Codestral 2508 · Qwen3 Coder", why: "SWE-bench, agents code" },
  { task: "Travail autonome long", models: "Claude Fable 5 · GLM 5.2 · Opus 4.8 · GPT-5.5", why: "Tâches multi-jours, agents" },
  { task: "Agents autonomes long contexte", models: "MiniMax 3 (M3) · GLM 5.2 · Kimi K2.7 Code", why: "1M tokens, tool use, agents" },
  { task: "Code local / économique", models: "Gemma 4 31B · Gemma 4 26B A4B", why: "Apache 2.0, 256K ctx, raisonnement" },
  { task: "Brainstorm créatif", models: "Grok 3/4 · Euryale · Dolphin Venice · MythoMax", why: "Peu de censure, idéation libre" },
  { task: "Rédaction marketing", models: "Sonnet 4.6 · GPT-5.4 · Kimi K2.6", why: "Ton naturel, créatif" },
  { task: "Triage / résumés", models: "Haiku 4.5 · GPT-5 Nano · GLM 4.5 Air", why: "Rapide, quasi gratuit" },
];

const BUDGET_RULES = [
  { emoji: "💰", label: "Économique", models: "MiniMax M2.7 · Nemotron 3 Nano · Haiku 4.5 · GLM 4.5 Air" },
  { emoji: "⚖️", label: "Équilibré", models: "Sonnet 4 · Mistral Medium 3.5 · DeepSeek V3.1 · Qwen3 Coder" },
  { emoji: "🧠", label: "Qualité max", models: "Opus 4.8 · GLM 5.2 · Kimi K2.7 Code · Nemotron 3 Ultra" },
];

const AVOID = [
  "Claude Nil n'existe pas encore sur OpenRouter (pas disponible dans la liste)",
  "Opus 4.8 / GPT-5 Pro pour le PM ou la QA (trop cher pour des tâches simples)",
  "Grok 3 pour des specs techniques au format strict",
];

export function ModelGuideCard() {
  const [open, setOpen] = useState(true);

  return (
    <div className="rounded-xl border border-copper/20 bg-white/[0.02]">
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        className="flex w-full items-center justify-between gap-3 px-4 py-3 text-left transition hover:bg-white/[0.03]"
      >
        <div className="flex items-center gap-2.5">
          <BookOpen className="h-4 w-4 text-copper" />
          <div>
            <p className="text-sm font-medium text-ivory/90">Guide — Quelle IA pour quel travail ?</p>
            <p className="text-[11px] text-titanium/50">
              Classés par usage : raisonnement · code · chat · rapide · non censuré
            </p>
          </div>
        </div>
        {open ? (
          <ChevronUp className="h-4 w-4 shrink-0 text-titanium/40" />
        ) : (
          <ChevronDown className="h-4 w-4 shrink-0 text-titanium/40" />
        )}
      </button>

      {open && (
        <div className="space-y-5 border-t border-white/5 px-4 py-4">
          {/* Budget rules */}
          <div className="grid gap-2 sm:grid-cols-3">
            {BUDGET_RULES.map((r) => (
              <div
                key={r.label}
                className="rounded-lg border border-white/8 bg-white/[0.02] px-3 py-2.5"
              >
                <p className="text-xs font-semibold text-ivory/80">
                  {r.emoji} {r.label}
                </p>
                <p className="mt-1 text-[11px] leading-relaxed text-titanium/60">{r.models}</p>
              </div>
            ))}
          </div>

          {/* By task */}
          <div>
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-titanium/40">
              Par type de travail
            </p>
            <div className="overflow-hidden rounded-lg border border-white/8">
              <table className="w-full text-left text-xs">
                <thead>
                  <tr className="border-b border-white/5 bg-white/[0.02]">
                    <th className="px-3 py-2 font-medium text-titanium/60">Tâche</th>
                    <th className="px-3 py-2 font-medium text-copper/80">Modèles recommandés</th>
                    <th className="hidden px-3 py-2 font-medium text-titanium/60 sm:table-cell">Pourquoi</th>
                  </tr>
                </thead>
                <tbody>
                  {TASK_RECS.map((row, i) => (
                    <tr
                      key={row.task}
                      className={cn(
                        "border-b border-white/5 last:border-0",
                        i % 2 === 0 ? "bg-transparent" : "bg-white/[0.01]"
                      )}
                    >
                      <td className="px-3 py-2 text-ivory/80">{row.task}</td>
                      <td className="px-3 py-2 text-copper/90">{row.models}</td>
                      <td className="hidden px-3 py-2 text-titanium/50 sm:table-cell">{row.why}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* By agent */}
          <div>
            <p className="mb-2 text-[10px] font-semibold uppercase tracking-widest text-titanium/40">
              Par bureau ALNUA
            </p>
            <div className="grid gap-1.5 sm:grid-cols-2">
              {AGENT_RECS.map((row) => (
                <div
                  key={row.agent}
                  className="flex items-baseline justify-between gap-2 rounded-lg border border-white/5 px-3 py-2"
                >
                  <span className="text-xs font-medium text-ivory/75">{row.agent}</span>
                  <span className="text-right text-[11px] text-titanium/55">
                    Auto → <span className="text-copper/80">{row.auto}</span>
                    {row.force && (
                      <>
                        <br />
                        <span className="text-titanium/40">Forcer : {row.force}</span>
                      </>
                    )}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Avoid */}
          <div className="rounded-lg border border-amber-500/15 bg-amber-500/5 px-3 py-2.5">
            <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-amber-400/70">
              À éviter
            </p>
            <ul className="space-y-1">
              {AVOID.map((item) => (
                <li key={item} className="text-[11px] text-titanium/55 before:mr-1.5 before:content-['·']">
                  {item}
                </li>
              ))}
            </ul>
          </div>

          <p className="text-[10px] text-titanium/35">
            Mode Auto = tier de l&apos;agent · Standard utilise DeepSeek V3.1 par défaut.
            Choisis un modèle par bureau dans les menus ci-dessous — c&apos;est sauvegardé automatiquement.
          </p>
        </div>
      )}
    </div>
  );
}
