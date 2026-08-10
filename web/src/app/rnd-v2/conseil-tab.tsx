"use client";

import { useMemo, useState } from "react";
import { Loader2 } from "lucide-react";
import { toast } from "sonner";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import {
  closeCouncilSession,
  evaluateCouncilProject,
  fetchCouncilGauges,
  postCouncilMessage,
  startCouncilSession,
  type CouncilGauges,
  type CouncilMessage,
  type CouncilVerdict,
} from "@/lib/rnd-council";
import { C } from "../app-v2/shared";

/* Conseil stratégique IA + Conseil IA (Phase 25, ROADMAP.md) — remplace
   l'ancien Brainstorm mono-agent. 3 colonnes : participants (gauche),
   conversation (centre), jauges live (droite). Le roster ci-dessous
   duplique volontairement agents/rnd_council_agent.py::COUNCIL_MEMBERS —
   c'est un affichage statique (avant qu'une session existe, l'API n'a rien
   à renvoyer), la session réelle renvoie `team` qui fait foi une fois
   démarrée. */

const COUNCIL_ROSTER = [
  { agent_id: "council_chair", name: "Selene Marchetti", role: "Présidente du Conseil" },
  { agent_id: "council_innovation", name: "Kai Osei", role: "Innovation & Vision" },
  { agent_id: "council_tech", name: "Freya Lindqvist", role: "Faisabilité & Ingénierie" },
  { agent_id: "council_business", name: "Darius Whitmore", role: "Business & Marché" },
  { agent_id: "council_data", name: "Amara Solis", role: "Données & Risques" },
] as const;

const VERDICT_COLOR: Record<CouncilVerdict, string> = {
  GO: "#2DD4BF",
  MAYBE: "#E0A95C",
  NO: "#f87171",
};

function GaugeBar({ label, value }: { label: string; value: number }) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center justify-between text-[10px]" style={{ color: C.warm }}>
        <span>{label}</span>
        <span style={{ color: C.ivory }}>{value}%</span>
      </div>
      <span className="block h-1.5 overflow-hidden rounded-full" style={{ background: "rgba(224,155,106,.15)" }}>
        <span
          className="block h-full rounded-full transition-[width] duration-700"
          style={{ width: `${value}%`, background: `linear-gradient(90deg,#B86E45,${C.copperLight})` }}
        />
      </span>
    </div>
  );
}

function EvaluateForm({
  onSubmit,
  busy,
}: {
  onSubmit: (input: { topic: string; budget: string; team: string; weeks: string; productType: string }) => void;
  busy: boolean;
}) {
  const [topic, setTopic] = useState("");
  const [budget, setBudget] = useState("");
  const [team, setTeam] = useState("");
  const [weeks, setWeeks] = useState("");
  const [productType, setProductType] = useState("");

  const inputCls = "w-full rounded-lg border px-2.5 py-1.5 text-[11px] outline-none";
  const inputStyle = { background: "rgba(8,7,6,.7)", borderColor: "rgba(224,155,106,.2)", color: C.ivory };

  return (
    <div className="flex flex-col gap-2.5 rounded-xl border p-4" style={{ borderColor: C.line, background: "#000000" }}>
      <p className="text-[10px] uppercase tracking-wider" style={{ color: C.faint }}>
        Évaluer un projet
      </p>
      <input
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
        placeholder="Projet en une phrase (ex : SaaS d'automatisation RH pour PME)"
        className={inputCls}
        style={inputStyle}
      />
      <div className="grid grid-cols-3 gap-2">
        <input value={budget} onChange={(e) => setBudget(e.target.value)} placeholder="Budget (€)" className={inputCls} style={inputStyle} />
        <input value={team} onChange={(e) => setTeam(e.target.value)} placeholder="Équipe (pers.)" className={inputCls} style={inputStyle} />
        <input value={weeks} onChange={(e) => setWeeks(e.target.value)} placeholder="Délai (sem.)" className={inputCls} style={inputStyle} />
      </div>
      <input
        value={productType}
        onChange={(e) => setProductType(e.target.value)}
        placeholder="Type de produit (SaaS, app mobile, hardware...)"
        className={inputCls}
        style={inputStyle}
      />
      <button
        type="button"
        disabled={busy || !topic.trim()}
        onClick={() => onSubmit({ topic, budget, team, weeks, productType })}
        className="flex items-center justify-center gap-2 rounded-lg border py-2 text-[11.5px] disabled:opacity-40"
        style={{ borderColor: "rgba(224,155,106,.45)", background: "rgba(224,155,106,.1)", color: C.copperLight }}
      >
        {busy ? <Loader2 className="h-3.5 w-3.5 animate-spin" /> : null}
        {busy ? "Le Conseil délibère…" : "Lancer le débat"}
      </button>
    </div>
  );
}

export function ConseilTab() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<CouncilMessage[]>([]);
  const [gauges, setGauges] = useState<CouncilGauges | null>(null);
  const [decision, setDecision] = useState<{ recommendation: CouncilVerdict; consensus_pct: number } | null>(null);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [mode, setMode] = useState<"chat" | "evaluate">("chat");

  const stanceByAgent = useMemo(() => {
    const map = new Map<string, { verdict: CouncilVerdict; stance_text: string }>();
    for (const a of gauges?.per_agent ?? []) map.set(a.agent_id, a);
    return map;
  }, [gauges]);

  async function handleSend() {
    const text = draft.trim();
    if (!text || busy) return;
    setBusy(true);
    setDraft("");
    try {
      let sid = sessionId;
      if (!sid) {
        const session = await startCouncilSession({ kind: "strategic", topic: text.slice(0, 80) });
        sid = session.session_id;
        setSessionId(sid);
      }
      const res = await postCouncilMessage(sid, text);
      setMessages((prev) => [...prev, ...res.messages].sort((a, b) => a.created_at.localeCompare(b.created_at)));
      const gaugesRes = await fetchCouncilGauges(sid);
      setGauges(gaugesRes);
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Le Conseil n'a pas pu répondre");
    } finally {
      setBusy(false);
    }
  }

  async function handleEvaluate(input: { topic: string; budget: string; team: string; weeks: string; productType: string }) {
    setBusy(true);
    try {
      const res = await evaluateCouncilProject({
        topic: input.topic,
        structured_input: {
          budget_eur: input.budget ? Number(input.budget) : null,
          team_size: input.team ? Number(input.team) : null,
          timeframe_weeks: input.weeks ? Number(input.weeks) : null,
          product_type: input.productType,
        },
      });
      setSessionId(res.session_id);
      setMessages(res.debate.messages);
      setGauges(res.gauges);
      setDecision({ recommendation: res.recommendation, consensus_pct: res.consensus_pct });
      setMode("chat");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Évaluation refusée");
    } finally {
      setBusy(false);
    }
  }

  async function handleClose() {
    if (!sessionId) return;
    setBusy(true);
    try {
      const res = await closeCouncilSession(sessionId);
      setGauges(res.gauges);
      if (res.deliberated) {
        setDecision({ recommendation: res.recommendation, consensus_pct: res.consensus_pct });
        toast.success(`Décision Collective : ${res.recommendation} (${res.consensus_pct}% consensus)`);
      } else {
        toast.error("Le Conseil n'a pas pu délibérer (aucune réponse des membres) — pas de décision à afficher.");
      }
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Clôture impossible");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto pb-2">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
          CONSEIL STRATÉGIQUE IA
        </p>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => setMode("chat")}
            className="rounded-full border px-2.5 py-1 text-[10px]"
            style={mode === "chat" ? { borderColor: "rgba(224,155,106,.45)", background: "rgba(224,155,106,.12)", color: C.copperLight } : { borderColor: C.lineSoft, color: C.faint }}
          >
            Discussion libre
          </button>
          <button
            type="button"
            onClick={() => setMode("evaluate")}
            className="rounded-full border px-2.5 py-1 text-[10px]"
            style={mode === "evaluate" ? { borderColor: "rgba(224,155,106,.45)", background: "rgba(224,155,106,.12)", color: C.copperLight } : { borderColor: C.lineSoft, color: C.faint }}
          >
            💎 Conseil IA — Évaluer un projet
          </button>
          {sessionId ? (
            <button
              type="button"
              onClick={() => void handleClose()}
              disabled={busy}
              className="rounded-full border px-2.5 py-1 text-[10px] disabled:opacity-40"
              style={{ borderColor: C.lineSoft, color: C.warm }}
            >
              Clôturer
            </button>
          ) : null}
        </div>
      </div>

      {decision ? (
        <div
          className="rounded-xl border p-3 text-center"
          style={{ borderColor: `${VERDICT_COLOR[decision.recommendation]}55`, background: `${VERDICT_COLOR[decision.recommendation]}14` }}
        >
          <p className="text-[10px] uppercase tracking-wider" style={{ color: C.faint }}>
            Décision Collective
          </p>
          <p className="text-[16px] font-bold" style={{ color: VERDICT_COLOR[decision.recommendation] }}>
            {decision.recommendation} — {decision.consensus_pct}% de consensus
          </p>
        </div>
      ) : null}

      {mode === "evaluate" && !decision ? (
        <EvaluateForm onSubmit={(input) => void handleEvaluate(input)} busy={busy} />
      ) : (
        <div className="grid min-h-[420px] flex-1 grid-cols-1 gap-3 min-[1100px]:grid-cols-[190px_1fr_220px]">
          {/* Participants */}
          <div className="flex flex-col gap-2 rounded-xl border p-2.5" style={{ borderColor: C.line, background: "#000000" }}>
            <p className="px-1 text-[9px] uppercase tracking-wider" style={{ color: C.faint }}>
              Participants
            </p>
            {COUNCIL_ROSTER.map((member) => {
              const stance = stanceByAgent.get(member.agent_id);
              return (
                <div key={member.agent_id} className="flex items-start gap-2 rounded-lg p-1.5" style={{ background: "rgba(255,255,255,.02)" }}>
                  <AgentAvatar agentId={member.agent_id} name={member.name} size={30} />
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-[10.5px] font-medium" style={{ color: C.ivory }}>
                      {member.name}
                    </p>
                    <p className="truncate text-[9px]" style={{ color: C.faint }}>
                      {member.role}
                    </p>
                    {stance ? (
                      <p className="mt-1 truncate text-[9.5px] italic" style={{ color: VERDICT_COLOR[stance.verdict] }}>
                        « {stance.stance_text} »
                      </p>
                    ) : null}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Conversation */}
          <div className="flex min-h-[320px] flex-col rounded-xl border" style={{ borderColor: C.line, background: "rgba(13,11,9,.5)" }}>
            <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-2.5 overflow-y-auto p-3">
              {messages.length === 0 ? (
                <p className="text-[11px]" style={{ color: C.faint }}>
                  Écris une question au Conseil pour démarrer la discussion — les 5 membres répondent en direct.
                </p>
              ) : (
                messages.map((m) => {
                  const roster = COUNCIL_ROSTER.find((r) => r.agent_id === m.speaker);
                  const isUser = m.role === "user";
                  return (
                    <div key={m.id} className={isUser ? "flex justify-end" : "flex justify-start"}>
                      <div
                        className="max-w-[85%] rounded-lg px-2.5 py-2"
                        style={{
                          background: isUser ? "rgba(224,155,106,.14)" : "rgba(255,255,255,.03)",
                          border: `1px solid ${isUser ? "rgba(224,155,106,.25)" : C.line}`,
                        }}
                      >
                        <p className="mb-1 text-[10px] font-semibold" style={{ color: isUser ? C.copperLight : C.warm }}>
                          {isUser ? "Emilie" : roster?.name ?? m.speaker}
                        </p>
                        <p className="text-[11px] leading-[1.5]" style={{ color: "#A7ADB5" }}>
                          {m.content}
                        </p>
                      </div>
                    </div>
                  );
                })
              )}
              {busy ? (
                <p className="flex items-center gap-2 text-[10.5px]" style={{ color: C.faint }}>
                  <Loader2 className="h-3 w-3 animate-spin" /> Le Conseil délibère…
                </p>
              ) : null}
            </div>
            {mode === "chat" ? (
              <div className="flex items-center gap-2 border-t px-3 py-2.5" style={{ borderColor: C.lineSoft }}>
                <input
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      void handleSend();
                    }
                  }}
                  placeholder="Pose une question au Conseil..."
                  disabled={busy}
                  className="min-w-0 flex-1 rounded-lg border px-3 py-2 text-[11px] outline-none disabled:opacity-50"
                  style={{ background: "rgba(8,7,6,.7)", borderColor: "rgba(224,155,106,.2)", color: C.ivory }}
                />
                <button
                  type="button"
                  onClick={() => void handleSend()}
                  disabled={busy || !draft.trim()}
                  className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border text-[13px] disabled:opacity-40"
                  style={{ borderColor: "rgba(224,155,106,.5)", background: "rgba(224,155,106,.14)", color: C.copperLight }}
                >
                  ↗
                </button>
              </div>
            ) : null}
          </div>

          {/* Jauges */}
          <div className="flex flex-col gap-3 dept-instrument p-3">
            <p className="text-[9px] uppercase tracking-wider" style={{ color: C.faint }}>
              Jauges du débat
            </p>
            {gauges ? (
              <>
                <GaugeBar label="Consensus" value={gauges.consensus_pct} />
                <GaugeBar label="Faisabilité" value={gauges.feasibility_pct} />
                <GaugeBar label="Innovation" value={gauges.innovation_pct} />
                <GaugeBar label="ROI" value={gauges.roi_pct} />
                <GaugeBar label="Risque" value={gauges.risk_pct} />
              </>
            ) : (
              <p className="text-[10px]" style={{ color: C.faint }}>
                Les jauges apparaissent dès que le Conseil a délibéré au moins une fois.
              </p>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
