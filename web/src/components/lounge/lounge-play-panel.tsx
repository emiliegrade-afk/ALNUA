"use client";

import { useEffect, useState } from "react";
import {
  ACTIVITY_LABELS,
  type LoungeActivityId,
} from "@/components/lounge/lounge-constants";
import {
  completeLoungeSession,
  proposeLoungeFinding,
  runLoungeSession,
  startLoungeSession,
  type LoungeDept,
  type LoungeSession,
} from "@/lib/lounge-api";

const QUICK_AGENTS = [
  { id: "dev_app", label: "Théo (APP)" },
  { id: "dev_backend", label: "Hao (Backend)" },
  { id: "dev_gaming", label: "Nova (Gaming)" },
  { id: "analyst_data", label: "Axel (Data)" },
  { id: "qa", label: "Alex (QA)" },
  { id: "brainstorm", label: "Idris (R&D)" },
] as const;

const DEPTS: { id: LoungeDept; label: string }[] = [
  { id: "app", label: "APP" },
  { id: "rd", label: "R&D" },
  { id: "gaming", label: "Gaming" },
  { id: "robo", label: "Robotique" },
  { id: "marketing", label: "Marketing" },
  { id: "hub", label: "Hub" },
];

type Props = {
  open: boolean;
  activity: LoungeActivityId;
  onClose: () => void;
  onSessionChange: () => void;
};

/** Panneau session multi-activité — Phase 46 V6. */
export function LoungePlayPanel({
  open,
  activity,
  onClose,
  onSessionChange,
}: Props) {
  const [agentId, setAgentId] = useState<string>(QUICK_AGENTS[0].id);
  const [session, setSession] = useState<LoungeSession | null>(null);
  const [answer, setAnswer] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dept, setDept] = useState<LoungeDept>("rd");
  const [summary, setSummary] = useState("");
  const [proposeMsg, setProposeMsg] = useState<string | null>(null);

  const label = ACTIVITY_LABELS[activity];

  useEffect(() => {
    if (!open) {
      setSession(null);
      setAnswer("");
      setError(null);
      setBusy(false);
      setSummary("");
      setProposeMsg(null);
    }
  }, [open, activity]);

  if (!open) return null;

  async function start(runNow: boolean) {
    setBusy(true);
    setError(null);
    setProposeMsg(null);
    try {
      const s = await startLoungeSession({
        agent_id: agentId,
        activity,
        run_now: runNow,
      });
      setSession(s);
      if (s.llm_error) setError(s.llm_error);
      onSessionChange();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Échec démarrage");
    } finally {
      setBusy(false);
    }
  }

  async function runLlm() {
    if (!session) return;
    setBusy(true);
    setError(null);
    try {
      const s = await runLoungeSession(session.id);
      setSession(s);
      onSessionChange();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Échec LLM");
    } finally {
      setBusy(false);
    }
  }

  async function submitAnswer() {
    if (!session || !answer.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const s = await completeLoungeSession(session.id, answer.trim());
      setSession(s);
      onSessionChange();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Échec validation");
    } finally {
      setBusy(false);
    }
  }

  async function propose() {
    if (!session || summary.trim().length < 8) return;
    setBusy(true);
    setError(null);
    try {
      const res = await proposeLoungeFinding({
        session_id: session.id,
        dept,
        summary: summary.trim(),
        agent_id: session.agent_id,
      });
      setProposeMsg(res.message);
      onSessionChange();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Échec proposition");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-obsidian-deep/70 p-4 sm:items-center">
      <div
        className="alnua-scroll max-h-[90vh] w-full max-w-lg overflow-y-auto border border-copper/35 bg-obsidian-2 p-4 shadow-[0_0_40px_rgba(224,155,106,0.12)]"
        role="dialog"
        aria-label={`${label} Lounge`}
      >
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="label-caps text-copper/80">{label}</p>
            <h3 className="mt-1 text-lg text-ivory">Challenge Lounge</h3>
            <p className="mt-1 text-xs text-titanium/55">
              Session isolée · LLM DeepSeek (Lounge) · pas de write prod.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="text-xs uppercase tracking-wide text-titanium/60 hover:text-copper"
          >
            Fermer
          </button>
        </div>

        {!session || session.status === "completed" ? (
          <div className="mt-4 space-y-3">
            {session?.status !== "completed" ? (
              <>
                <label className="block text-[11px] uppercase tracking-[0.12em] text-titanium/50">
                  Agent
                  <select
                    value={agentId}
                    onChange={(e) => setAgentId(e.target.value)}
                    className="mt-1 w-full border border-titanium/25 bg-obsidian px-2 py-2 text-sm text-ivory"
                  >
                    {QUICK_AGENTS.map((a) => (
                      <option key={a.id} value={a.id}>
                        {a.label}
                      </option>
                    ))}
                  </select>
                </label>
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void start(false)}
                    className="border border-copper/45 px-3 py-2 text-[11px] uppercase tracking-[0.14em] text-copper hover:bg-copper/15 disabled:opacity-40"
                  >
                    Lancer session
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void start(true)}
                    className="border border-copper/70 bg-copper/15 px-3 py-2 text-[11px] uppercase tracking-[0.14em] text-copper hover:bg-copper/25 disabled:opacity-40"
                  >
                    Lancer + résoudre (LLM)
                  </button>
                </div>
              </>
            ) : null}
          </div>
        ) : null}

        {session ? (
          <div className="mt-4 space-y-3 border-t border-titanium/15 pt-4">
            <p className="text-sm font-medium text-ivory">
              {session.puzzle_title}{" "}
              <span className="text-titanium/45">· {session.agent_id}</span>
            </p>
            <p className="text-xs leading-relaxed text-titanium/75">
              {session.puzzle_prompt}
            </p>
            {session.status === "active" ? (
              <>
                <textarea
                  value={answer}
                  onChange={(e) => setAnswer(e.target.value)}
                  rows={activity === "creative" || activity === "exploration" ? 4 : 2}
                  placeholder="Ta réponse (ou laisse l’agent LLM)"
                  className="w-full border border-titanium/25 bg-obsidian px-2 py-2 text-sm text-ivory"
                />
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={busy || !answer.trim()}
                    onClick={() => void submitAnswer()}
                    className="border border-copper/45 px-3 py-2 text-[11px] uppercase tracking-[0.14em] text-copper hover:bg-copper/15 disabled:opacity-40"
                  >
                    Valider
                  </button>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => void runLlm()}
                    className="border border-titanium/35 px-3 py-2 text-[11px] uppercase tracking-[0.14em] text-titanium hover:border-copper/40 hover:text-copper disabled:opacity-40"
                  >
                    Résoudre via agent
                  </button>
                </div>
              </>
            ) : (
              <>
                <div
                  className={`border px-3 py-2 text-sm ${
                    session.won
                      ? "border-copper/40 text-copper"
                      : "border-titanium/25 text-titanium/70"
                  }`}
                >
                  {session.won ? "Challenge gagné" : "Session terminée"}
                  {session.points_awarded != null
                    ? ` · +${session.points_awarded} XP Lounge`
                    : ""}
                  {session.correct_answer ? (
                    <span className="mt-1 block text-[11px] text-titanium/50">
                      Réponse : {session.correct_answer}
                    </span>
                  ) : null}
                </div>
                <p className="label-caps text-titanium/55">Proposer au département</p>
                <select
                  value={dept}
                  onChange={(e) => setDept(e.target.value as LoungeDept)}
                  className="w-full border border-titanium/25 bg-obsidian px-2 py-2 text-sm text-ivory"
                >
                  {DEPTS.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.label}
                    </option>
                  ))}
                </select>
                <textarea
                  value={summary}
                  onChange={(e) => setSummary(e.target.value)}
                  rows={3}
                  placeholder="Idée / insight à transmettre (min. 8 car.)"
                  className="w-full border border-titanium/25 bg-obsidian px-2 py-2 text-sm text-ivory"
                />
                <button
                  type="button"
                  disabled={busy || summary.trim().length < 8}
                  onClick={() => void propose()}
                  className="border border-copper/50 px-3 py-2 text-[11px] uppercase tracking-[0.14em] text-copper hover:bg-copper/15 disabled:opacity-40"
                >
                  Créer ticket (validation CEO)
                </button>
                {proposeMsg ? (
                  <p className="text-xs text-copper/90">{proposeMsg}</p>
                ) : null}
              </>
            )}
          </div>
        ) : null}

        {error ? (
          <p className="mt-3 text-xs text-amber-200/90">{error}</p>
        ) : null}
        {busy ? (
          <p className="mt-2 text-[11px] text-titanium/45">En cours…</p>
        ) : null}
      </div>
    </div>
  );
}

/** @deprecated alias — use LoungePlayPanel */
export function LoungePuzzlePanel(props: Omit<Props, "activity"> & { activity?: LoungeActivityId }) {
  return <LoungePlayPanel {...props} activity={props.activity ?? "puzzle"} />;
}
