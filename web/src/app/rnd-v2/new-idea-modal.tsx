"use client";

import { useState } from "react";
import { Loader2, X } from "lucide-react";
import { toast } from "sonner";
import { injectRndIdea, runDeepResearch, type DeepResearchReport } from "@/lib/rnd";
import { C } from "../app-v2/shared";

/* "+ Nouvelle idée" (demande Emilie, 2026-07-31) — bouton déjà visible dans
   la barre de commandes de rnd-v2 mais purement décoratif jusqu'ici. Deux
   modes, tous les deux réutilisent une capacité backend réelle qui
   n'était jamais branchée sur aucune UI (ni /rd, ni rnd-v2) :
   - "Proposer une idée" → injectRndIdea (déjà existant, utilisé par
     l'ancienne page /rd) — ajout brut au Pipeline, scoré au prochain
     cycle R&D (pas de score immédiat, volontairement honnête).
   - "Lancer une recherche" → services/deep_research.py::run_deep_research
     (jamais exposé côté UI avant) — pipeline multi-rounds réel, affiche le
     rapport tel quel, ne crée PAS d'idée automatiquement. */

type Mode = "idea" | "research";

const inputCls = "w-full rounded-lg border px-2.5 py-2 text-[11px] outline-none";
const inputStyle = { background: "rgba(8,7,6,.7)", borderColor: "rgba(224,155,106,.2)", color: "#F5F2EA" };

const RESEARCH_AGENTS = [
  { id: "brainstorm", label: "Idris — Brainstorm" },
  { id: "rnd_agent", label: "Alex — R&D technique" },
  { id: "analyst_business", label: "Layla — Business" },
] as const;

function ResearchReportView({ report }: { report: DeepResearchReport }) {
  return (
    <div className="alnua-scroll flex max-h-[420px] flex-col gap-3 overflow-y-auto pr-1">
      <div className="rounded-lg border p-3" style={{ borderColor: C.line, background: "rgba(22,17,13,.4)" }}>
        <p className="text-[9px] uppercase tracking-wider" style={{ color: C.faint }}>
          Synthèse — {report.rounds_completed} round{report.rounds_completed > 1 ? "s" : ""} ({report.depth})
        </p>
        <p className="mt-1.5 text-[11.5px] leading-[1.5]" style={{ color: "#A7ADB5" }}>
          {report.executive_summary}
        </p>
      </div>

      {report.key_findings.length > 0 ? (
        <div>
          <p className="mb-1.5 text-[9px] uppercase tracking-wider" style={{ color: C.faint }}>
            Constats clés
          </p>
          <ul className="flex flex-col gap-1.5">
            {report.key_findings.map((f, i) => (
              <li key={i} className="rounded-lg border p-2 text-[10.5px]" style={{ borderColor: C.lineSoft, color: "#A7ADB5" }}>
                {f.finding}
                <span className="ml-1.5 text-[9px]" style={{ color: C.faint }}>
                  ({f.confidence}{f.source ? ` · ${f.source}` : ""})
                </span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {report.recommended_actions.length > 0 ? (
        <div>
          <p className="mb-1.5 text-[9px] uppercase tracking-wider" style={{ color: C.faint }}>
            Actions recommandées
          </p>
          <ul className="flex flex-col gap-1 text-[10.5px]" style={{ color: "#A7ADB5" }}>
            {report.recommended_actions.map((a, i) => (
              <li key={i}>→ {a}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {report.knowledge_gaps.length > 0 ? (
        <div>
          <p className="mb-1.5 text-[9px] uppercase tracking-wider" style={{ color: C.faint }}>
            Zones d&apos;ombre
          </p>
          <ul className="flex flex-col gap-1 text-[10.5px]" style={{ color: C.faint }}>
            {report.knowledge_gaps.map((g, i) => (
              <li key={i}>· {g}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

export function NewIdeaModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  const [mode, setMode] = useState<Mode>("idea");
  const [ideaText, setIdeaText] = useState("");
  const [query, setQuery] = useState("");
  const [rounds, setRounds] = useState(2);
  const [agentId, setAgentId] = useState<(typeof RESEARCH_AGENTS)[number]["id"]>("brainstorm");
  const [busy, setBusy] = useState(false);
  const [report, setReport] = useState<DeepResearchReport | null>(null);

  if (!open) return null;

  function reset() {
    setIdeaText("");
    setQuery("");
    setReport(null);
    setMode("idea");
  }

  async function handleSubmitIdea() {
    if (!ideaText.trim()) return;
    setBusy(true);
    try {
      const res = await injectRndIdea(ideaText.trim());
      toast.success(`« ${res.title} » ajoutée au Pipeline — sera scorée au prochain cycle R&D.`);
      reset();
      onClose();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Échec de l'ajout");
    } finally {
      setBusy(false);
    }
  }

  async function handleRunResearch() {
    if (!query.trim()) return;
    setBusy(true);
    setReport(null);
    try {
      const res = await runDeepResearch({ query: query.trim(), rounds, agent_id: agentId });
      setReport(res);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "La recherche a échoué");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ background: "rgba(6,7,10,.82)" }}
      onClick={() => {
        reset();
        onClose();
      }}
    >
      <div
        className="flex w-full max-w-[560px] flex-col gap-4 rounded-2xl border p-5"
        style={{ borderColor: C.lineStrong, background: "#0B0C0E" }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setMode("idea")}
              className="rounded-full border px-3 py-1.5 text-[10.5px]"
              style={mode === "idea" ? { borderColor: "rgba(224,155,106,.45)", background: "rgba(224,155,106,.12)", color: C.copperLight } : { borderColor: C.lineSoft, color: C.faint }}
            >
              💡 Proposer une idée
            </button>
            <button
              type="button"
              onClick={() => setMode("research")}
              className="rounded-full border px-3 py-1.5 text-[10.5px]"
              style={mode === "research" ? { borderColor: "rgba(224,155,106,.45)", background: "rgba(224,155,106,.12)", color: C.copperLight } : { borderColor: C.lineSoft, color: C.faint }}
            >
              🔎 Lancer une recherche
            </button>
          </div>
          <button
            type="button"
            onClick={() => {
              reset();
              onClose();
            }}
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full border"
            style={{ borderColor: C.line, color: C.warm }}
            aria-label="Fermer"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>

        {mode === "idea" ? (
          <>
            <p className="text-[10.5px]" style={{ color: C.faint }}>
              Ajoutée directement au Pipeline — pas de score avant le prochain cycle R&D (honnête, pas de note fabriquée).
            </p>
            <textarea
              value={ideaText}
              onChange={(e) => setIdeaText(e.target.value)}
              placeholder="Décris l'idée en quelques phrases..."
              rows={5}
              className={`${inputCls} resize-none`}
              style={inputStyle}
            />
            <button
              type="button"
              disabled={busy || !ideaText.trim()}
              onClick={() => void handleSubmitIdea()}
              className="flex items-center justify-center gap-2 rounded-lg border py-2 text-[11.5px] disabled:opacity-40"
              style={{ borderColor: "rgba(224,155,106,.45)", background: "rgba(224,155,106,.1)", color: C.copperLight }}
            >
              {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
              Ajouter au Pipeline
            </button>
          </>
        ) : (
          <>
            <p className="text-[10.5px]" style={{ color: C.faint }}>
              Recherche multi-rounds réelle (explore → approfondit → vérifie) — ne crée pas d&apos;idée automatiquement, juste un rapport.
            </p>
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Thème à explorer (ex : agents IA embarqués sur smartphone)"
              className={inputCls}
              style={inputStyle}
            />
            <div className="flex gap-2">
              <select
                value={agentId}
                onChange={(e) => setAgentId(e.target.value as typeof agentId)}
                className={inputCls}
                style={inputStyle}
              >
                {RESEARCH_AGENTS.map((a) => (
                  <option key={a.id} value={a.id}>
                    {a.label}
                  </option>
                ))}
              </select>
              <select
                value={rounds}
                onChange={(e) => setRounds(Number(e.target.value))}
                className={inputCls}
                style={{ ...inputStyle, maxWidth: 140 }}
              >
                <option value={1}>1 round (rapide)</option>
                <option value={2}>2 rounds</option>
                <option value={3}>3 rounds (approfondi)</option>
              </select>
            </div>
            <button
              type="button"
              disabled={busy || !query.trim()}
              onClick={() => void handleRunResearch()}
              className="flex items-center justify-center gap-2 rounded-lg border py-2 text-[11.5px] disabled:opacity-40"
              style={{ borderColor: "rgba(224,155,106,.45)", background: "rgba(224,155,106,.1)", color: C.copperLight }}
            >
              {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
              {busy ? "Les agents explorent…" : "Lancer la recherche"}
            </button>
            {report ? <ResearchReportView report={report} /> : null}
          </>
        )}
      </div>
    </div>
  );
}
