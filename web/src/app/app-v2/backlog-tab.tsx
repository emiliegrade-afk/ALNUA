"use client";

import { useMemo, useState } from "react";
import { updateTicket, type TicketWithProject } from "@/lib/tickets";
import { CreateTicketModal } from "@/components/tickets/create-ticket-modal";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import type { BureauAgentDef } from "@/lib/agent-bureau";
import type { ConsoleActivityItem } from "@/lib/console/types";
import type { Project } from "@/lib/types";
import { C, KIND_META } from "./shared";

/* Backlog — tableau d'idées. Les tickets réels n'ont qu'un statut "open" pour
 * tout ce qui n'est pas démarré : les 5 colonnes "pré-rejet" sont donc une
 * subdivision provisoire de ce seul statut (hash stable de l'id du ticket,
 * pas de tirage aléatoire) — seule la colonne REJETÉES est réelle (statut
 * `wont_fix`). Le donut de répartition par type est 100% réel (champ `type`
 * du ticket). Votes, sprint, dépendance : provisoires, commentés. Décision
 * du 2026-07-30. */

function hash(seed: string): number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  return h;
}

const STAGES = ["Nouvelles idées", "À prioriser", "En attente", "Validées", "Planifiées"] as const;
type Stage = (typeof STAGES)[number] | "Rejetées";

const TYPE_LABEL: Record<string, string> = {
  feature: "Fonctionnalités",
  improvement: "Amélioration",
  bug: "Corrections",
  crash: "Corrections",
};
const TYPE_COLOR: Record<string, string> = {
  feature: C.online,
  improvement: C.copperLight,
  bug: "#A7ADB5",
  crash: "#A7ADB5",
};
const TYPE_ICON: Record<string, string> = {
  feature: "💡",
  improvement: "✨",
  bug: "🐞",
  crash: "🐞",
};

function stageOf(ticket: TicketWithProject): Stage {
  if (ticket.status === "wont_fix") return "Rejetées";
  return STAGES[hash(ticket.id) % STAGES.length];
}

function relTime(iso: string) {
  const days = Math.floor((Date.now() - new Date(iso).getTime()) / 86_400_000);
  if (days <= 0) return "aujourd'hui";
  if (days === 1) return "hier";
  return `${days} j`;
}

function IdeaCard({
  ticket,
  agents,
  onReject,
}: {
  ticket: TicketWithProject;
  agents: BureauAgentDef[];
  onReject: (ticket: TicketWithProject) => void;
}) {
  const stage = stageOf(ticket);
  const author = agents.length > 0 ? agents[hash(`${ticket.id}-author`) % agents.length] : undefined;
  const votes = 8 + (hash(`${ticket.id}-votes`) % 30);
  const sprint = 18 + (hash(`${ticket.id}-sprint`) % 6);
  const hasDependency = hash(`${ticket.id}-dep`) % 4 === 0;

  return (
    <div className="rounded-lg border p-2.5" style={{ borderColor: C.line, background: "rgba(13,11,9,.5)" }}>
      <div className="flex items-start justify-between gap-2">
        <p className="min-w-0 flex-1 text-[11px] leading-snug" style={{ color: C.ivory }}>
          <span className="mr-1">{TYPE_ICON[ticket.type] ?? "📝"}</span>
          {ticket.title}
        </p>
        {stage !== "Rejetées" ? (
          <button
            type="button"
            onClick={() => onReject(ticket)}
            aria-label={`Rejeter « ${ticket.title} »`}
            className="shrink-0 text-[10px]"
            style={{ color: "rgba(248,113,113,.5)" }}
          >
            ✕
          </button>
        ) : null}
      </div>
      <span
        className="mt-1.5 inline-flex items-center gap-1 rounded-full border px-1.5 py-px text-[8.5px]"
        style={{ borderColor: "rgba(200,127,78,.2)", color: TYPE_COLOR[ticket.type] ?? C.faint }}
      >
        <span className="h-1 w-1 rounded-full" style={{ background: TYPE_COLOR[ticket.type] ?? C.faint }} />
        {TYPE_LABEL[ticket.type] ?? ticket.type}
      </span>
      <div className="mt-2 flex items-center justify-between gap-2">
        {author ? (
          <span className="flex min-w-0 items-center gap-1.5">
            <AgentAvatar agentId={author.id} name={author.name} size={16} />
            <span className="truncate text-[8.5px]" style={{ color: C.faint }}>
              {author.name.split(" ")[0]} · {relTime(ticket.created_at)}
            </span>
          </span>
        ) : (
          <span />
        )}
        {stage === "Rejetées" ? (
          <span className="shrink-0 text-[8.5px]" style={{ color: "#f87171" }}>
            Rejetée · {relTime(ticket.updated_at)}
          </span>
        ) : stage === "Validées" ? (
          <span className="shrink-0 text-[11px]" style={{ color: C.online }}>
            ✓
          </span>
        ) : stage === "Planifiées" ? (
          <span className="shrink-0 text-[8.5px]" style={{ color: C.copperLight }}>
            Sprint {sprint}
          </span>
        ) : stage === "En attente" ? (
          <span
            className="shrink-0 rounded-full border px-1.5 py-px text-[8px]"
            style={{ borderColor: "rgba(200,127,78,.25)", color: C.warm }}
          >
            {hasDependency ? "Dépendance" : "En attente"}
          </span>
        ) : (
          <span className="shrink-0 text-[8.5px]" style={{ color: C.dim }}>
            ↑ {votes}
          </span>
        )}
      </div>
    </div>
  );
}

function DonutChart({ segments }: { segments: { color: string; count: number }[] }) {
  const total = segments.reduce((s, seg) => s + seg.count, 0);
  const r = 26;
  const circ = 2 * Math.PI * r;
  let acc = 0;
  return (
    <svg width="64" height="64" viewBox="0 0 64 64">
      <circle cx="32" cy="32" r={r} fill="none" stroke="rgba(200,127,78,.1)" strokeWidth="9" />
      {total > 0
        ? segments
            .filter((s) => s.count > 0)
            .map((s, i) => {
              const frac = s.count / total;
              const dash = `${(frac * circ).toFixed(2)} ${circ.toFixed(2)}`;
              const offset = -acc * circ;
              acc += frac;
              return (
                <circle key={i} cx="32" cy="32" r={r} fill="none" stroke={s.color} strokeWidth="9" strokeDasharray={dash} strokeDashoffset={offset} transform="rotate(-90 32 32)" />
              );
            })
        : null}
    </svg>
  );
}

export function BacklogTab({
  tickets,
  loading,
  onChange,
  projects,
  agents,
  activityFeed,
}: {
  tickets: TicketWithProject[];
  loading: boolean;
  onChange: (t: TicketWithProject[]) => void;
  projects: Project[];
  agents: BureauAgentDef[];
  activityFeed: ConsoleActivityItem[];
}) {
  const [createOpen, setCreateOpen] = useState(false);

  const backlogTickets = useMemo(
    () => tickets.filter((t) => t.status === "open" || t.status === "wont_fix"),
    [tickets],
  );

  const buckets = useMemo(() => {
    const map: Record<Stage, TicketWithProject[]> = {
      "Nouvelles idées": [],
      "À prioriser": [],
      "En attente": [],
      Validées: [],
      Planifiées: [],
      Rejetées: [],
    };
    for (const t of backlogTickets) map[stageOf(t)].push(t);
    return map;
  }, [backlogTickets]);

  const typeCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const t of backlogTickets) counts[t.type] = (counts[t.type] ?? 0) + 1;
    return counts;
  }, [backlogTickets]);

  async function reject(ticket: TicketWithProject) {
    const before = tickets;
    onChange(tickets.map((t) => (t.id === ticket.id ? { ...t, status: "wont_fix" } : t)));
    try {
      await updateTicket(ticket.id, { status: "wont_fix" });
    } catch {
      onChange(before);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[220px] flex-1 items-center justify-center rounded-xl text-[11px]" style={{ border: `1px solid ${C.line}`, color: C.faint }}>
        Chargement du backlog…
      </div>
    );
  }

  const donutSegments = [
    { color: TYPE_COLOR.feature, count: typeCounts.feature ?? 0 },
    { color: TYPE_COLOR.bug, count: (typeCounts.bug ?? 0) + (typeCounts.crash ?? 0) },
    { color: TYPE_COLOR.improvement, count: typeCounts.improvement ?? 0 },
  ];
  const donutTotal = donutSegments.reduce((s, seg) => s + seg.count, 0);

  return (
    <div className="flex min-h-0 flex-1 gap-3 overflow-y-auto">
      <div className="flex min-w-0 flex-1 flex-col gap-4">
        <div className="flex items-center justify-between gap-3">
          <div className="min-w-0">
            <h2 className="truncate text-[18px] font-bold tracking-[0.5px]" style={{ color: C.ivory }}>
              BACKLOG
            </h2>
            <p className="truncate text-[10.5px]" style={{ color: C.dim }}>
              Toutes les idées, demandes et améliorations en attente de priorisation
            </p>
          </div>
          <button
            type="button"
            onClick={() => setCreateOpen(true)}
            className="shrink-0 rounded-[18px] border px-3.5 py-1.5 text-[11px]"
            style={{ borderColor: "rgba(200,127,78,.45)", background: "rgba(200,127,78,.12)", color: C.copperLight }}
          >
            ＋ Nouvelle idée
          </button>
        </div>

        <div className="flex gap-2.5">
          <div className="grid flex-1 grid-cols-4 gap-2.5">
            {[
              { label: "Items au total", value: backlogTickets.length },
              { label: "Nouvelles idées", value: buckets["Nouvelles idées"].length },
              { label: "À prioriser", value: buckets["À prioriser"].length },
              { label: "Déjà planifiés", value: buckets["Planifiées"].length },
            ].map((s) => (
              <div key={s.label} className="rounded-xl border p-3 text-center" style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}>
                <p className="text-[20px] font-semibold" style={{ color: C.ivory }}>
                  {s.value}
                </p>
                <p className="text-[8.5px]" style={{ color: C.faint }}>
                  {s.label}
                </p>
              </div>
            ))}
          </div>
          <div className="flex shrink-0 items-center gap-3 rounded-xl border px-4 py-2" style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}>
            <DonutChart segments={donutSegments} />
            <div className="flex flex-col gap-1 text-[9px]" style={{ color: C.warm }}>
              <p className="mb-0.5" style={{ color: C.faint }}>
                Répartition par type
              </p>
              <span className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full" style={{ background: TYPE_COLOR.feature }} />
                Fonctionnalités {donutTotal > 0 ? Math.round(((typeCounts.feature ?? 0) / donutTotal) * 100) : 0}%
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full" style={{ background: TYPE_COLOR.bug }} />
                Corrections {donutTotal > 0 ? Math.round((((typeCounts.bug ?? 0) + (typeCounts.crash ?? 0)) / donutTotal) * 100) : 0}%
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full" style={{ background: TYPE_COLOR.improvement }} />
                Amélioration {donutTotal > 0 ? Math.round(((typeCounts.improvement ?? 0) / donutTotal) * 100) : 0}%
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 xl:grid-cols-3">
          {([...STAGES, "Rejetées"] as Stage[]).map((stage) => (
            <div key={stage} className="flex min-h-[200px] flex-col rounded-xl border" style={{ borderColor: C.line, background: "rgba(16,13,11,.5)" }}>
              <div className="flex items-center justify-between border-b px-3 py-2.5" style={{ borderColor: C.lineSoft }}>
                <span className="text-[9px] tracking-[1.2px]" style={{ color: C.copperLight }}>
                  {stage.toUpperCase()}
                </span>
                <span className="text-[10px]" style={{ color: C.faint }}>
                  {buckets[stage].length}
                </span>
              </div>
              <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto p-2.5">
                {buckets[stage].length === 0 ? (
                  <p className="py-4 text-center text-[9.5px]" style={{ color: C.faint }}>
                    Aucune idée.
                  </p>
                ) : (
                  buckets[stage].map((t) => <IdeaCard key={t.id} ticket={t} agents={agents} onReject={(tk) => void reject(tk)} />)
                )}
              </div>
              <button
                type="button"
                onClick={() => setCreateOpen(true)}
                className="border-t px-3 py-2 text-center text-[10px]"
                style={{ borderColor: C.lineSoft, color: C.warm }}
              >
                + Ajouter une idée
              </button>
            </div>
          ))}
        </div>
      </div>

      <div className="hidden w-[clamp(220px,17vw,270px)] shrink-0 flex-col gap-3 min-[1200px]:flex">
        <div className="rounded-xl border p-3.5" style={{ borderColor: C.line, background: "rgba(16,13,11,.55)" }}>
          <p className="mb-2.5 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            ACTIVITÉ RÉCENTE
          </p>
          <div className="flex flex-col gap-2.5">
            {activityFeed.length === 0 ? (
              <p className="py-4 text-center text-[10px]" style={{ color: C.faint }}>
                Aucune activité récente.
              </p>
            ) : (
              activityFeed.slice(0, 8).map((ev) => {
                const meta = KIND_META[ev.kind] ?? KIND_META.create;
                return (
                  <div key={ev.id} className="flex items-start gap-2">
                    <AgentAvatar agentId={ev.agent} name={ev.agent} size={22} />
                    <span className="min-w-0 flex-1">
                      <span className="block text-[10px] leading-[1.35]" style={{ color: C.warm }}>
                        <span style={{ color: C.ivory }}>{ev.agent}</span> {ev.action}
                      </span>
                      <span className="text-[8.5px]" style={{ color: meta.color }}>
                        {ev.time}
                      </span>
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </div>
      </div>

      <CreateTicketModal
        open={createOpen}
        onOpenChange={setCreateOpen}
        projects={projects}
        onCreated={(t) => onChange([...tickets, t])}
        agents={agents}
      />
    </div>
  );
}
