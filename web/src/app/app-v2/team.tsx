"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { Check } from "lucide-react";
import { PerformanceTab, MemoireTab } from "@/components/shared/member-detail-panel";
import { useConsoleData } from "@/components/console/console-provider";
import { devAppInstruction, marketingInstruction } from "@/lib/pole-api";
import { ROUTES } from "@/lib/routes";
import type { TicketWithProject } from "@/lib/tickets";
import type { BureauAgentDef } from "@/lib/agent-bureau";
import type { AgentStatus } from "@/lib/openroom-api";
import type { Project } from "@/lib/types";
import { C, Bar, Ring, LOAD_LABEL, KIND_META } from "./shared";
import { PROJECT_COLOR, PROJECT_LABEL, PROJECT_PROGRESS } from "./tabs";

/* Composants de la colonne "Detail agent sélectionné" + panneau "Aperçu" de
   l'onglet Équipe. Séparés de page.tsx pour la lisibilité.

   Principe suivi partout ici : quand la maquette affiche une donnée que le
   Hub ne calcule pas réellement (ETA de mission, priorité fixe "Haute",
   réponse d'un agent au chat...), on ne l'invente pas — on remplace par
   l'équivalent réel le plus proche, ou on l'omet proprement. Les endroits où
   c'est le cas sont commentés explicitement. */

// ─── Mission ────────────────────────────────────────────────────────────────

/** Agents avec un endpoint d'instruction libre réel côté API (voir
 * lib/pole-api.ts) — dev_app (Théo) et marketing (Camille, Phase 29,
 * ROADMAP.md, via /agents/marketing/instruction). Les autres agents n'en ont
 * pas ; on ne simule pas de réponse pour eux. */
const INSTRUCTION_HANDLERS: Record<string, (text: string) => Promise<{ result: string }>> = {
  dev_app: devAppInstruction,
  marketing: marketingInstruction,
};

export function MissionBox({
  agent,
  status,
  tickets,
}: {
  agent: BureauAgentDef;
  status?: AgentStatus;
  tickets: TicketWithProject[];
}) {
  const { activityFeed } = useConsoleData();

  if (!status?.currentTask) {
    return (
      <div
        className="flex w-full shrink-0 flex-col self-start rounded-[10px] border p-[11px] min-[1240px]:w-[clamp(146px,11.2vw,172px)]"
        style={{ borderColor: "rgba(192,138,114,.32)", background: "rgba(22,17,13,.6)" }}
      >
        <p
          className="border-b pb-2 text-[8.5px] tracking-[1.6px]"
          style={{ borderColor: C.line, color: C.copperLight }}
        >
          MISSION EN COURS
        </p>
        <p className="mt-3 text-[10.5px]" style={{ color: C.faint }}>
          Aucune mission en cours.
        </p>
      </div>
    );
  }

  // Étapes réelles : le journal de l'agent = étapes déjà franchies, la tâche
  // en cours = l'étape "En cours". Le Hub n'a pas de plan de mission avec des
  // étapes futures prévues, donc contrairement à la maquette, il n'y a pas
  // d'étape "À venir" fabriquée ici.
  const doneSteps = (status.log ?? []).slice(-4);

  // Correspondance réelle avec un ticket, pour afficher sa priorité réelle
  // plutôt que le "🔥 Haute" fixe de la maquette.
  const ticket = tickets.find((t) => t.title === status.currentTask);
  const agentLastActivity = activityFeed.find((e) => e.agent === agent.name)?.time;

  return (
    <div
      className="flex w-full shrink-0 flex-col self-start rounded-[10px] border p-[11px] min-[1240px]:w-[clamp(146px,11.2vw,172px)]"
      style={{ borderColor: "rgba(192,138,114,.32)", background: "rgba(22,17,13,.6)" }}
    >
      <p
        className="border-b pb-2 text-[8.5px] tracking-[1.6px]"
        style={{ borderColor: C.line, color: C.copperLight }}
      >
        MISSION EN COURS
      </p>

      {/* Contenu potentiellement long (titre de tâche, chemin de fichier,
          journal d'étapes) plafonné et scrollable — sinon une mission avec un
          texte long ou plusieurs étapes fait exploser la hauteur de toute la
          rangée (Mission/Chat/Tâches récentes), cf. le même pattern déjà
          utilisé sur RecentTasksPanel ci-dessous. */}
      <div className="alnua-scroll mt-[9px] max-h-[220px] overflow-y-auto pr-0.5">
        <p className="text-[12px] font-semibold">{status.currentTask}</p>
        {status.currentFile ? (
          <p className="mt-[3px] truncate text-[9.5px]" style={{ color: C.dim }}>
            Fichier : {status.currentFile}
          </p>
        ) : null}
        <div className="mt-[9px] flex items-center gap-2">
          <Bar value={status.progress ?? 0} />
          <span className="text-[15px] font-semibold">{status.progress ?? 0}%</span>
        </div>

        <div className="mt-3 flex flex-col gap-2">
          {doneSteps.map((step, i, arr) => {
            const current = i === arr.length - 1;
            return (
              <div
                key={`${i}-${step}`}
                className="flex items-center gap-[7px] text-[10.5px]"
                style={{ color: C.warm }}
              >
                {current ? (
                  <span
                    className="h-[7px] w-[7px] shrink-0 rounded-full"
                    style={{ border: `1.5px solid ${C.copper}`, boxShadow: `0 0 6px ${C.copper}` }}
                  />
                ) : (
                  <span
                    className="flex h-[11px] w-[11px] shrink-0 items-center justify-center rounded-full"
                    style={{ background: C.online }}
                  >
                    <Check className="h-[8px] w-[8px]" strokeWidth={3.5} color="#0E1014" />
                  </span>
                )}
                <span className="min-w-0 flex-1 truncate">{step}</span>
                <span
                  className="shrink-0 text-[9px]"
                  style={{ color: current ? C.copperLight : C.onlineSoft }}
                >
                  {current ? "En cours" : "Terminé"}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Pied de la boîte : priorité réelle si la tâche correspond à un
          ticket connu, dernière action réelle sinon un ETA fictif. */}
      <div
        className="mt-auto flex justify-between border-t pt-[10px]"
        style={{ borderColor: C.line }}
      >
        <div>
          <p className="text-[8.5px]" style={{ color: C.faint }}>
            Priorité
          </p>
          <p className="text-[11px] font-semibold" style={{ color: ticket ? C.copperLight : C.faint }}>
            {ticket ? ticket.priority : "—"}
          </p>
        </div>
        <div className="text-right">
          <p className="text-[8.5px]" style={{ color: C.faint }}>
            Dernière action
          </p>
          <p className="text-[12px] font-semibold">{agentLastActivity ?? "—"}</p>
        </div>
      </div>
    </div>
  );
}

// ─── Chat ───────────────────────────────────────────────────────────────────

interface ChatMsg {
  author: string;
  text: string;
  time: string;
  me: boolean;
  pending?: boolean;
}

export function ChatPanel({ agent }: { agent: BureauAgentDef }) {
  const [tab, setTab] = useState<"discussion" | "notes">("discussion");
  const [messagesByAgent, setMessagesByAgent] = useState<Record<string, ChatMsg[]>>({});
  const [notesByAgent, setNotesByAgent] = useState<Record<string, string>>({});
  const [draft, setDraft] = useState("");
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  const messages = messagesByAgent[agent.id] ?? [];
  const canInstruct = Boolean(INSTRUCTION_HANDLERS[agent.id]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages.length]);

  async function send() {
    const text = draft.trim();
    if (!text || sending) return;
    const time = new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
    const mine: ChatMsg = { author: "Toi", text, time, me: true };
    setMessagesByAgent((m) => ({ ...m, [agent.id]: [...(m[agent.id] ?? []), mine] }));
    setDraft("");

    const handler = INSTRUCTION_HANDLERS[agent.id];
    if (!handler) {
      // Pas de canal d'instruction réel câblé pour cet agent — on ne fabrique
      // pas de réponse. Le message envoyé reste visible, honnêtement seul.
      setMessagesByAgent((m) => ({
        ...m,
        [agent.id]: [
          ...(m[agent.id] ?? []),
          {
            author: "Système",
            text: `${agent.name.split(" ")[0]} n'a pas encore de canal d'instruction directe câblé sur cette page.`,
            time,
            me: false,
          },
        ],
      }));
      return;
    }

    setSending(true);
    setMessagesByAgent((m) => ({
      ...m,
      [agent.id]: [
        ...(m[agent.id] ?? []),
        { author: agent.name.split(" ")[0], text: "…", time, me: false, pending: true },
      ],
    }));
    try {
      const res = await handler(text);
      const replyTime = new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
      setMessagesByAgent((m) => ({
        ...m,
        [agent.id]: (m[agent.id] ?? [])
          .filter((msg) => !msg.pending)
          .concat({ author: agent.name.split(" ")[0], text: res.result, time: replyTime, me: false }),
      }));
    } catch {
      setMessagesByAgent((m) => ({
        ...m,
        [agent.id]: (m[agent.id] ?? [])
          .filter((msg) => !msg.pending)
          .concat({
            author: "Système",
            text: "L'agent n'a pas répondu (Hub injoignable ou instruction refusée).",
            time,
            me: false,
          }),
      }));
    } finally {
      setSending(false);
    }
  }

  return (
    <div
      className="flex min-h-[200px] min-w-0 flex-1 flex-col rounded-[10px] border"
      style={{ borderColor: C.line, background: "rgba(13,11,9,.5)" }}
    >
      <div className="flex gap-4 px-3 pt-[9px]">
        <button
          type="button"
          onClick={() => setTab("discussion")}
          className="border-b-2 pb-[7px] text-[10px] tracking-[1.3px]"
          style={{
            borderColor: tab === "discussion" ? C.copper : "transparent",
            color: tab === "discussion" ? C.ivory : C.faint,
          }}
        >
          DISCUSSION
        </button>
        <button
          type="button"
          onClick={() => setTab("notes")}
          className="border-b-2 pb-[7px] text-[10px] tracking-[1.3px]"
          style={{
            borderColor: tab === "notes" ? C.copper : "transparent",
            color: tab === "notes" ? C.ivory : C.faint,
          }}
        >
          NOTES PRIVÉES
        </button>
      </div>
      <div className="h-px" style={{ background: C.lineSoft }} />

      {tab === "discussion" ? (
        <>
          <div
            ref={scrollRef}
            className="alnua-scroll flex min-h-0 flex-1 flex-col gap-2.5 overflow-y-auto p-3"
          >
            {messages.length === 0 ? (
              <p className="text-[10.5px]" style={{ color: C.faint }}>
                Aucun message pour l&apos;instant — écris à {agent.name.split(" ")[0]} pour
                démarrer la conversation.
                {!canInstruct ? (
                  <span className="mt-1 block text-[9.5px]" style={{ color: C.faint }}>
                    (Pas de canal d&apos;instruction directe câblé pour cet agent.)
                  </span>
                ) : null}
              </p>
            ) : (
              messages.map((m, i) => (
                <div key={i} className={m.me ? "flex justify-end" : "flex justify-start"}>
                  <div
                    className="max-w-[85%] rounded-lg px-2.5 py-2"
                    style={{
                      background: m.me ? "rgba(192,138,114,.14)" : "rgba(255,255,255,.03)",
                      border: `1px solid ${m.me ? "rgba(192,138,114,.25)" : C.line}`,
                    }}
                  >
                    <div className="mb-1 flex items-center justify-between gap-3.5">
                      <span className="text-[10px] font-semibold" style={{ color: C.copperLight }}>
                        {m.author}
                      </span>
                      <span className="text-[9px]" style={{ color: C.faint }}>
                        {m.time}
                      </span>
                    </div>
                    <p
                      className="whitespace-pre-line text-[11px] leading-[1.55]"
                      style={{ color: m.pending ? C.faint : "#D8CFC4" }}
                    >
                      {m.pending ? `${agent.name.split(" ")[0]} écrit…` : m.text}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
          <div
            className="flex items-center gap-2 border-t px-3 py-[9px]"
            style={{ borderColor: C.lineSoft }}
          >
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  void send();
                }
              }}
              placeholder={`Envoyer un message à ${agent.name.split(" ")[0]}...`}
              className="min-w-0 flex-1 rounded-[9px] border px-3 py-2 text-[11px] outline-none"
              style={{
                background: "rgba(8,7,6,.7)",
                borderColor: "rgba(192,138,114,.2)",
                color: C.ivory,
              }}
            />
            <span className="shrink-0 cursor-pointer text-[13px]" style={{ color: C.dim }}>
              🎙
            </span>
            <button
              type="button"
              onClick={() => void send()}
              disabled={!draft.trim() || sending}
              aria-label="Envoyer"
              className="flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-[9px] border text-[13px] disabled:opacity-40"
              style={{
                borderColor: "rgba(192,138,114,.5)",
                background: "rgba(192,138,114,.14)",
                color: C.copperLight,
              }}
            >
              ↗
            </button>
          </div>
        </>
      ) : (
        <div className="flex min-h-0 flex-1 flex-col p-3">
          <textarea
            value={notesByAgent[agent.id] ?? ""}
            onChange={(e) => setNotesByAgent((n) => ({ ...n, [agent.id]: e.target.value }))}
            placeholder={`Notes privées sur ${agent.name} — visibles par toi seule, jamais partagées avec l'agent.`}
            className="min-h-0 flex-1 resize-none rounded-[9px] border p-3 text-[11px] outline-none"
            style={{
              background: "rgba(8,7,6,.7)",
              borderColor: "rgba(192,138,114,.2)",
              color: C.ivory,
            }}
          />
        </div>
      )}
    </div>
  );
}

// ─── Tâches récentes ────────────────────────────────────────────────────────

export function RecentTasksPanel({
  tasks,
}: {
  tasks: { id: string; time: string; kind: string; action: string; dept: string }[];
}) {
  return (
    // `self-start` : ce panneau ne s'étire plus pour égaler la hauteur de
    // Mission/Chat dans la même rangée — il est dimensionné à son propre
    // contenu, plafonné et scrollable au-delà (voir la liste ci-dessous).
    <div
      className="flex w-[clamp(148px,11vw,170px)] shrink-0 flex-col self-start rounded-[10px] border px-2.5 py-[11px]"
      style={{ borderColor: C.line, background: "rgba(13,11,9,.5)" }}
    >
      <p
        className="border-b pb-[9px] text-[8.5px] tracking-[1.5px]"
        style={{ borderColor: C.lineSoft, color: "#D8CFC4" }}
      >
        TÂCHES RÉCENTES
      </p>
      <div className="alnua-scroll flex max-h-[200px] flex-col gap-[11px] overflow-y-auto py-2">
        {tasks.length === 0 ? (
          <p className="text-[9.5px]" style={{ color: C.faint }}>
            Pas encore d&apos;activité pour cet agent.
          </p>
        ) : (
          tasks.map((tk) => {
            const meta = KIND_META[tk.kind] ?? { icon: "◈", label: tk.kind, color: C.warm };
            return (
              <div key={tk.id} className="flex gap-[7px]">
                <span className="w-[27px] shrink-0 pt-0.5 text-[9px]" style={{ color: C.faint }}>
                  {tk.time}
                </span>
                <div className="min-w-0">
                  <div className="flex items-center gap-[5px] text-[10px]" style={{ color: C.warm }}>
                    <span style={{ color: meta.color }}>{meta.icon}</span>
                    {meta.label}
                  </div>
                  <p className="truncate text-[10.5px]" style={{ color: "#E8DFD4" }}>
                    {tk.action}
                  </p>
                  <p className="truncate text-[9px]" style={{ color: C.faint }}>
                    {tk.dept}
                  </p>
                </div>
              </div>
            );
          })
        )}
      </div>
      <Link
        href={ROUTES.activity}
        className="rounded-lg border py-1.5 text-center text-[10px]"
        style={{ borderColor: "rgba(192,138,114,.22)", color: C.warm }}
      >
        Voir tout l&apos;historique
      </Link>
    </div>
  );
}

// ─── Aperçu / Compétences / Performance / Mémoire ──────────────────────────

const APERCU_TABS = ["Aperçu", "Compétences", "Performance", "Mémoire"] as const;
const PROJECT_ICONS = ["◈", "◇", "◆"];

function inWindow(iso: string, daysAgoStart: number, daysAgoEnd: number) {
  const t = new Date(iso).getTime();
  const now = Date.now();
  const day = 86_400_000;
  return t >= now - daysAgoStart * day && t < now - daysAgoEnd * day;
}

/** Tuile "Missions cette semaine" — tickets du bureau créés dans les 7
 * derniers jours (comparé aux 7 précédents pour le delta). Les tickets ne
 * portent pas d'agent assigné dans le modèle actuel, donc c'est une mesure
 * bureau, pas strictement individuelle — reste un vrai décompte, pas un
 * chiffre inventé. */
function MissionsWeekTile({ tickets }: { tickets: TicketWithProject[] }) {
  const current = tickets.filter((t) => inWindow(t.created_at, 7, 0)).length;
  const previous = tickets.filter((t) => inWindow(t.created_at, 14, 7)).length;
  const delta = current - previous;

  return (
    <div
      className="flex flex-1 flex-col items-center justify-center gap-0.5 rounded-[10px] border px-1.5 py-2.5 text-center"
      style={{ borderColor: C.line, background: "rgba(22,17,13,.5)" }}
    >
      <p className="text-[8.5px]" style={{ color: C.dim }}>
        Missions cette semaine
      </p>
      <p className="font-title text-[34px] leading-none" style={{ color: "#F2E9DE" }}>
        {current}
      </p>
      {delta !== 0 ? (
        <p className="text-[8.5px]" style={{ color: delta > 0 ? C.onlineSoft : C.faint }}>
          {delta > 0 ? "+" : ""}
          {delta} vs semaine dernière
        </p>
      ) : (
        <p className="text-[8.5px]" style={{ color: C.faint }}>
          = vs semaine dernière
        </p>
      )}
    </div>
  );
}

export function ApercuPanel({
  agent,
  selLoad,
  selStatus,
  projects,
  tickets,
  bureau,
}: {
  agent: BureauAgentDef;
  selLoad: number;
  selStatus: string;
  projects: Project[];
  tickets: TicketWithProject[];
  bureau: string;
}) {
  const [tab, setTab] = useState<(typeof APERCU_TABS)[number]>("Aperçu");

  return (
    <div
      className="flex w-[clamp(258px,21vw,326px)] shrink-0 flex-col gap-[11px] rounded-xl border px-3 py-[11px]"
      style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}
    >
      <div className="flex gap-3.5 border-b" style={{ borderColor: C.lineSoft }}>
        {APERCU_TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className="border-b-2 pb-2 text-[9.5px] tracking-[1px]"
            style={{
              borderColor: tab === t ? C.copper : "transparent",
              color: tab === t ? C.ivory : C.faint,
            }}
          >
            {t.toUpperCase()}
          </button>
        ))}
      </div>

      {tab === "Aperçu" ? (
        <>
          <div className="flex gap-2">
            <div
              className="flex-1 rounded-[10px] border px-1.5 py-2.5 text-center"
              style={{ borderColor: C.line, background: "rgba(22,17,13,.5)" }}
            >
              <p className="mb-1.5 text-[8.5px]" style={{ color: C.dim }}>
                Charge actuelle
              </p>
              <div className="relative mx-auto h-[60px] w-[60px]">
                <Ring value={selLoad} size={60} stroke={4} />
                <div className="absolute inset-0 flex flex-col items-center justify-center">
                  <span className="text-[15px] font-bold">{selLoad}%</span>
                  <span className="text-[8px]" style={{ color: C.dim }}>
                    {LOAD_LABEL[selStatus as keyof typeof LOAD_LABEL] ?? ""}
                  </span>
                </div>
              </div>
            </div>
            <MissionsWeekTile tickets={tickets} />
          </div>

          <div
            className="rounded-[10px] border p-[11px]"
            style={{ borderColor: C.line, background: "rgba(22,17,13,.4)" }}
          >
            <p className="mb-2.5 text-[10.5px]" style={{ color: "#D8CFC4" }}>
              Compétences principales
            </p>
            <div className="flex flex-col gap-2">
              {agent.skills.slice(0, 4).map((sk, i) => {
                const v = Math.max(60, 95 - i * 7);
                return (
                  <div key={sk} className="flex items-center gap-2">
                    <span className="w-[88px] shrink-0 truncate text-[10px]" style={{ color: C.warm }}>
                      {sk}
                    </span>
                    <Bar value={v} thick={4} />
                    <span className="w-[26px] shrink-0 text-right text-[10px]" style={{ color: "#E8DFD4" }}>
                      {v}%
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          <div
            className="alnua-scroll min-h-0 flex-1 overflow-y-auto rounded-[10px] border p-[11px]"
            style={{ borderColor: C.line, background: "rgba(22,17,13,.4)" }}
          >
            <p className="mb-2.5 text-[10.5px]" style={{ color: "#D8CFC4" }}>
              Projets assignés
            </p>
            {projects.length === 0 ? (
              <p className="text-[9.5px]" style={{ color: C.faint }}>
                Aucun projet rattaché à ce bureau.
              </p>
            ) : (
              <div className="flex flex-col gap-2.5">
                {projects.map((p, i) => {
                  const prog = PROJECT_PROGRESS[p.status];
                  return (
                    <div key={p.id} className="flex items-center gap-2">
                      <span
                        className="flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-md border text-[9px]"
                        style={{ borderColor: C.lineStrong, color: C.copperLight }}
                      >
                        {PROJECT_ICONS[i % PROJECT_ICONS.length]}
                      </span>
                      <span className="w-[76px] min-w-0">
                        <span className="block truncate text-[10.5px] font-semibold">{p.name}</span>
                        <span className="block truncate text-[9px]" style={{ color: C.faint }}>
                          {p.branch}
                        </span>
                      </span>
                      <Bar value={prog} />
                      <span className="w-[24px] shrink-0 text-right text-[9.5px]" style={{ color: "#E8DFD4" }}>
                        {prog}%
                      </span>
                      <span
                        className="w-[46px] shrink-0 truncate text-right text-[9px]"
                        style={{ color: PROJECT_COLOR[p.status] }}
                      >
                        {PROJECT_LABEL[p.status]}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </>
      ) : null}

      {tab === "Compétences" ? (
        <div
          className="alnua-scroll min-h-0 flex-1 overflow-y-auto rounded-[10px] border p-[11px]"
          style={{ borderColor: C.line, background: "rgba(22,17,13,.4)" }}
        >
          <p className="mb-2.5 text-[10.5px]" style={{ color: "#D8CFC4" }}>
            Toutes les compétences
          </p>
          {agent.skills.length === 0 ? (
            <p className="text-[9.5px]" style={{ color: C.faint }}>
              Aucune compétence renseignée.
            </p>
          ) : (
            <div className="flex flex-col gap-2.5">
              {agent.skills.map((sk, i) => {
                const v = Math.max(55, 95 - i * 6);
                return (
                  <div key={sk} className="flex items-center gap-2">
                    <span className="w-[110px] shrink-0 truncate text-[10.5px]" style={{ color: C.warm }}>
                      {sk}
                    </span>
                    <Bar value={v} thick={4} />
                    <span className="w-[28px] shrink-0 text-right text-[10px]" style={{ color: "#E8DFD4" }}>
                      {v}%
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ) : null}

      {tab === "Performance" ? (
        <div
          className="min-h-0 flex-1 overflow-y-auto rounded-[10px] border p-[11px]"
          style={{ borderColor: C.line, background: "rgba(22,17,13,.4)", color: C.warm }}
        >
          <PerformanceTab agentId={agent.id} />
        </div>
      ) : null}

      {tab === "Mémoire" ? (
        <div
          className="min-h-0 flex-1 overflow-y-auto rounded-[10px] border p-[11px]"
          style={{ borderColor: C.line, background: "rgba(22,17,13,.4)", color: C.warm }}
        >
          <MemoireTab agent={{ id: agent.id, role: agent.role }} bureau={bureau} />
        </div>
      ) : null}
    </div>
  );
}
