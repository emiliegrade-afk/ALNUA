"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchTicketsList, updateTicket, type TicketWithProject } from "@/lib/tickets";
import { TICKET_STATUSES, TICKET_PRIORITIES, TYPE_STYLES, type TicketStatus, type TicketPriority } from "@/components/tickets/tickets.constants";
import { CreateTicketModal } from "@/components/tickets/create-ticket-modal";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { getAgentById, type BureauAgentDef } from "@/lib/agent-bureau";
import type { AgentStatus } from "@/lib/openroom-api";
import type { ConsoleActivityItem } from "@/lib/console/types";
import type { Project } from "@/lib/types";
import { C, STATUS_LOAD, KIND_META, formatDueDate } from "../app-v2/shared";
import { hash, pick } from "./mock-data";

/* Missions Robotique — même structure que Missions App/Gaming (stats, board,
 * vue par priorité, chronologie, colonne filtres/charge/risques/performance),
 * avec des tags Composant/Banc de test en plus. Depuis la Phase 12
 * (ROADMAP.md, 2026-07-30), assigné/points/échéance sont de vrais champs du
 * ticket — fallback pseudo* pour les tickets créés avant cette phase. */

const BOARD_COLUMNS: { status: TicketStatus; label: string }[] = [
  { status: "open", label: "À FAIRE" },
  { status: "in_progress", label: "EN COURS" },
  { status: "in_review", label: "EN TEST" },
  { status: "done", label: "TERMINÉES" },
];

const PRIORITY_LABEL: Record<TicketPriority, string> = {
  critical: "Haute",
  high: "Haute",
  medium: "Moyenne",
  low: "Basse",
};

const COMPONENTS = ["Servo X2", "Carte PCB v3", "Batterie Li-ion", "Caméra IA", "Capteur LiDAR", "Châssis alu"] as const;
const BENCHES = ["Banc thermique", "Banc vibratoire", "Banc électrique", "Salle blanche"] as const;

function missionMeta(ticketId: string) {
  return {
    component: pick(`${ticketId}-comp`, COMPONENTS),
    bench: hash(`${ticketId}-bench`) % 2 === 0 ? pick(`${ticketId}-benchtag`, BENCHES) : null,
  };
}

function pseudoAssignee(ticketId: string, agents: BureauAgentDef[]): BureauAgentDef | undefined {
  if (agents.length === 0) return undefined;
  return agents[hash(ticketId) % agents.length];
}
function pseudoPoints(ticketId: string): number {
  return 2 + (hash(`${ticketId}-pts`) % 7);
}
function pseudoProgress(ticketId: string): number {
  return 15 + (hash(`${ticketId}-prog`) % 80);
}

interface MockRisk {
  id: string;
  title: string;
  detail: string;
  level: "Risque élevé" | "Risque moyen";
}

function risksFromTickets(tickets: TicketWithProject[]): MockRisk[] {
  const candidates = tickets.filter((t) => t.status === "in_progress" || t.status === "in_review").slice(0, 3);
  const details = ["Délai fournisseur", "Composant en rupture", "Certification bloquante"];
  return candidates.map((t, i) => ({
    id: t.id,
    title: t.title,
    detail: details[i % details.length],
    level: hash(`${t.id}-risk`) % 3 === 0 ? "Risque moyen" : "Risque élevé",
  }));
}

function TicketCard({
  ticket,
  agents,
  onMove,
  canMoveBack,
  canMoveForward,
}: {
  ticket: TicketWithProject;
  agents: BureauAgentDef[];
  onMove: (dir: 1 | -1) => void;
  canMoveBack: boolean;
  canMoveForward: boolean;
}) {
  const assignee = (ticket.assignee_agent_id && getAgentById(ticket.assignee_agent_id)) || pseudoAssignee(ticket.id, agents);
  const points = ticket.story_points ?? pseudoPoints(ticket.id);
  const due = ticket.due_date ? formatDueDate(ticket.due_date) : null;
  const typeLabel = TYPE_STYLES[ticket.type as keyof typeof TYPE_STYLES]?.label ?? ticket.type;
  const meta = missionMeta(ticket.id);

  return (
    <div className="rounded-lg border p-2.5" style={{ borderColor: C.line, background: "rgba(13,11,9,.5)" }}>
      <p className="text-[11px] leading-snug" style={{ color: C.ivory }}>
        {ticket.title}
      </p>
      <div className="mt-1 flex items-center justify-between gap-2">
        <p className="min-w-0 flex-1 truncate text-[9px]" style={{ color: C.faint }}>
          {ticket.project_name ?? "—"} / {typeLabel}
        </p>
        {due ? (
          <span className="shrink-0 text-[8.5px]" style={{ color: due.overdue ? "#f87171" : C.faint }}>
            📅 {due.label}
          </span>
        ) : null}
      </div>
      <div className="mt-1.5 flex flex-wrap gap-1">
        <span className="rounded-full border px-1.5 py-px text-[8px]" style={{ borderColor: "rgba(192,138,114,.2)", color: C.warm }}>
          🔧 {meta.component}
        </span>
        {meta.bench ? (
          <span className="rounded-full border px-1.5 py-px text-[8px]" style={{ borderColor: "rgba(192,138,114,.2)", color: C.warm }}>
            🧪 {meta.bench}
          </span>
        ) : null}
      </div>
      <div className="mt-2 flex items-center justify-between gap-2">
        {assignee ? (
          <span className="flex min-w-0 items-center gap-1.5">
            <AgentAvatar agentId={assignee.id} name={assignee.name} size={18} />
            <span className="truncate text-[9px]" style={{ color: C.warm }}>
              {assignee.name.split(" ")[0]}
            </span>
          </span>
        ) : (
          <span />
        )}
        {ticket.status === "done" ? (
          <span className="flex items-center gap-1 text-[9.5px]" style={{ color: C.online }}>
            100% ✓
          </span>
        ) : ticket.status === "in_progress" || ticket.status === "in_review" ? (
          <span className="flex items-center gap-1.5">
            <span className="h-1 w-10 overflow-hidden rounded-full" style={{ background: "rgba(192,138,114,.18)" }}>
              <span className="block h-full rounded-full" style={{ width: `${pseudoProgress(ticket.id)}%`, background: C.copper }} />
            </span>
            <span className="text-[9px]" style={{ color: C.dim }}>
              {pseudoProgress(ticket.id)}%
            </span>
          </span>
        ) : (
          <span className="text-[9px]" style={{ color: C.dim }}>
            {points} pts
          </span>
        )}
      </div>
      <div className="mt-1.5 flex items-center justify-between border-t pt-1.5" style={{ borderColor: C.lineSoft }}>
        <button type="button" disabled={!canMoveBack} onClick={() => onMove(-1)} aria-label={`Reculer « ${ticket.title} »`} className="h-5 w-5 rounded text-[10px] disabled:opacity-0" style={{ color: C.faint }}>
          ‹
        </button>
        <span className="text-[8.5px] uppercase" style={{ color: C.faint }}>
          {ticket.priority}
        </span>
        <button type="button" disabled={!canMoveForward} onClick={() => onMove(1)} aria-label={`Avancer « ${ticket.title} »`} className="h-5 w-5 rounded text-[10px] disabled:opacity-0" style={{ color: C.copperLight }}>
          ›
        </button>
      </div>
    </div>
  );
}

export function MissionsTab({
  projects,
  agents,
  statuses,
  activityFeed,
}: {
  projects: Project[];
  agents: BureauAgentDef[];
  statuses: Record<string, AgentStatus>;
  activityFeed: ConsoleActivityItem[];
}) {
  const [tickets, setTickets] = useState<TicketWithProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<"board" | "liste">("board");
  const [priorityFocus, setPriorityFocus] = useState<"Haute" | "Moyenne" | "Basse" | "À venir" | null>(null);
  const [search, setSearch] = useState("");
  const [projectFilter, setProjectFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState<"all" | TicketStatus>("all");
  const [priorityFilter, setPriorityFilter] = useState<"all" | TicketPriority>("all");
  const [createOpen, setCreateOpen] = useState(false);
  const [createDefaultProject, setCreateDefaultProject] = useState<string | undefined>(undefined);

  useEffect(() => {
    if (projects.length === 0) {
      setTickets([]);
      setLoading(false);
      return;
    }
    let cancelled = false;
    const ids = new Set(projects.map((p) => p.id));
    fetchTicketsList({ limit: 100 })
      .then((all) => {
        if (!cancelled) setTickets(all.filter((t) => ids.has(t.project_id)));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [projects]);

  const filtered = useMemo(() => {
    return tickets.filter((t) => {
      if (search && !t.title.toLowerCase().includes(search.toLowerCase())) return false;
      if (projectFilter !== "all" && t.project_id !== projectFilter) return false;
      if (statusFilter !== "all" && t.status !== statusFilter) return false;
      if (priorityFilter !== "all" && t.priority !== priorityFilter) return false;
      if (priorityFocus) {
        if (priorityFocus === "À venir") {
          if (t.status !== "open") return false;
        } else if (PRIORITY_LABEL[t.priority as TicketPriority] !== priorityFocus) {
          return false;
        }
      }
      return true;
    });
  }, [tickets, search, projectFilter, statusFilter, priorityFilter, priorityFocus]);

  const counts = {
    total: tickets.length,
    open: tickets.filter((t) => t.status === "open").length,
    in_progress: tickets.filter((t) => t.status === "in_progress").length,
    in_review: tickets.filter((t) => t.status === "in_review").length,
    done: tickets.filter((t) => t.status === "done" || t.status === "wont_fix").length,
  };

  const priorityBuckets: { key: "Haute" | "Moyenne" | "Basse" | "À venir"; items: TicketWithProject[] }[] = [
    { key: "Haute", items: tickets.filter((t) => t.priority === "critical" || t.priority === "high") },
    { key: "Moyenne", items: tickets.filter((t) => t.priority === "medium") },
    { key: "Basse", items: tickets.filter((t) => t.priority === "low") },
    { key: "À venir", items: tickets.filter((t) => t.status === "open") },
  ];

  const risks = useMemo(() => risksFromTickets(tickets), [tickets]);
  const efficiency = tickets.length > 0 ? Math.round((counts.done / tickets.length) * 100) : 0;
  const estimatedHours = tickets.length * 8;
  const spentHours = Math.round(estimatedHours * (efficiency / 100 || 0.6));

  function openCreateFor(projectId?: string) {
    setCreateDefaultProject(projectId);
    setCreateOpen(true);
  }

  async function moveTicket(ticket: TicketWithProject, dir: 1 | -1) {
    const idx = BOARD_COLUMNS.findIndex((c) => c.status === ticket.status);
    const next = BOARD_COLUMNS[idx + dir];
    if (!next) return;
    const before = tickets;
    setTickets(tickets.map((t) => (t.id === ticket.id ? { ...t, status: next.status } : t)));
    try {
      await updateTicket(ticket.id, { status: next.status });
    } catch {
      setTickets(before);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[220px] flex-1 items-center justify-center rounded-xl text-[11px]" style={{ border: `1px solid ${C.line}`, color: C.faint }}>
        Chargement des missions…
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 gap-3 overflow-y-auto pb-2">
      <div className="flex min-w-0 flex-1 flex-col gap-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-3">
            <span
              className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[10px] border text-[13px]"
              style={{ borderColor: "rgba(192,138,114,.4)", background: "radial-gradient(circle at 30% 20%, rgba(192,138,114,.25), rgba(19,22,27,.9))", color: C.copperLight }}
            >
              ◈
            </span>
            <div className="min-w-0">
              <h2 className="truncate text-[18px] font-bold tracking-[0.5px]" style={{ color: C.ivory }}>
                MISSIONS
              </h2>
              <p className="truncate text-[10.5px]" style={{ color: C.dim }}>
                Hardware, firmware, tests et assemblage
              </p>
            </div>
          </div>
          <div className="flex shrink-0 items-center gap-2">
            <span className="flex overflow-hidden rounded-lg border" style={{ borderColor: C.line }}>
              {(["board", "liste"] as const).map((v) => (
                <button
                  key={v}
                  type="button"
                  onClick={() => setView(v)}
                  className="px-3 py-1.5 text-[10.5px]"
                  style={{ background: view === v ? "rgba(192,138,114,.18)" : "transparent", color: view === v ? C.copperLight : C.faint }}
                >
                  {v === "board" ? "Vue Board" : "Vue Liste"}
                </button>
              ))}
            </span>
            <button
              type="button"
              onClick={() => openCreateFor(projects[0]?.id)}
              className="rounded-[18px] border px-3.5 py-1.5 text-[11px]"
              style={{ borderColor: "rgba(192,138,114,.45)", background: "rgba(192,138,114,.12)", color: C.copperLight }}
            >
              ＋ Nouvelle mission
            </button>
          </div>
        </div>

        <div className="grid grid-cols-5 gap-2.5">
          {[
            { label: "Missions au total", value: counts.total },
            { label: "En cours", value: counts.in_progress },
            { label: "En attente", value: counts.open },
            { label: "En test", value: counts.in_review },
            { label: "Terminées", value: counts.done },
          ].map((s) => (
            <div key={s.label} className="rounded-xl border p-3 text-center" style={{ borderColor: C.line, background: "rgba(19,22,27,.55)" }}>
              <p className="text-[20px] font-semibold" style={{ color: C.ivory }}>
                {s.value}
              </p>
              <p className="text-[8.5px]" style={{ color: C.faint }}>
                {s.label}
              </p>
            </div>
          ))}
        </div>

        {view === "board" ? (
          <section>
            <p className="mb-2 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
              BOARD DES MISSIONS
            </p>
            <div className="grid grid-cols-2 gap-3 xl:grid-cols-4">
              {BOARD_COLUMNS.map((col, colIdx) => {
                const items = filtered.filter((t) => t.status === col.status);
                return (
                  <div key={col.status} className="flex min-h-[200px] flex-col rounded-xl border" style={{ borderColor: C.line, background: "rgba(19,22,27,.5)" }}>
                    <div className="flex items-center justify-between border-b px-3 py-2.5" style={{ borderColor: C.lineSoft }}>
                      <span className="text-[9px] tracking-[1.2px]" style={{ color: C.copperLight }}>
                        {col.label}
                      </span>
                      <span className="text-[10px]" style={{ color: C.faint }}>
                        {items.length}
                      </span>
                    </div>
                    <div className="alnua-scroll flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto p-2.5">
                      {items.map((t) => (
                        <TicketCard key={t.id} ticket={t} agents={agents} onMove={(dir) => void moveTicket(t, dir)} canMoveBack={colIdx > 0} canMoveForward={colIdx < BOARD_COLUMNS.length - 1} />
                      ))}
                    </div>
                    <button type="button" onClick={() => openCreateFor(projects[0]?.id)} className="border-t px-3 py-2 text-center text-[10px]" style={{ borderColor: C.lineSoft, color: C.warm }}>
                      + Nouvelle mission
                    </button>
                  </div>
                );
              })}
            </div>
          </section>
        ) : (
          <section className="flex flex-col gap-1.5">
            {filtered.map((t) => (
              <div key={t.id} className="flex items-center gap-3 rounded-lg border px-3 py-2" style={{ borderColor: C.line }}>
                <span className="w-16 shrink-0 text-[9px] uppercase" style={{ color: C.copperLight }}>
                  {t.priority}
                </span>
                <span className="min-w-0 flex-1 truncate text-[11px]" style={{ color: C.ivory }}>
                  {t.title}
                </span>
                <span className="w-24 shrink-0 truncate text-[9.5px]" style={{ color: C.faint }}>
                  {t.project_name ?? "—"}
                </span>
                <span className="w-20 shrink-0 text-[9.5px]" style={{ color: C.dim }}>
                  {TICKET_STATUSES.find((s) => s.id === t.status)?.label ?? t.status}
                </span>
              </div>
            ))}
          </section>
        )}

        <section>
          <p className="mb-2 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            VUE PAR PRIORITÉ
          </p>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            {priorityBuckets.map((b) => (
              <div key={b.key} className="flex flex-col gap-2 rounded-xl border p-3" style={{ borderColor: C.line, background: "rgba(19,22,27,.5)" }}>
                <span className="text-[10.5px] font-medium" style={{ color: C.warm }}>
                  {b.key}
                </span>
                <div className="flex flex-col gap-1.5">
                  {b.items.slice(0, 3).map((t) => (
                    <div key={t.id} className="flex items-center justify-between gap-2 text-[9.5px]">
                      <span className="min-w-0 flex-1 truncate" style={{ color: C.ivory }}>
                        {t.title}
                      </span>
                      <span style={{ color: C.faint }}>{TICKET_STATUSES.find((s) => s.id === t.status)?.label}</span>
                    </div>
                  ))}
                  {b.items.length === 0 ? (
                    <p className="text-[9px]" style={{ color: C.faint }}>
                      Aucune mission.
                    </p>
                  ) : null}
                </div>
                <button
                  type="button"
                  onClick={() => setPriorityFocus(priorityFocus === b.key ? null : b.key)}
                  className="mt-1 rounded-lg border py-1 text-[9.5px]"
                  style={{ borderColor: priorityFocus === b.key ? C.copper : "rgba(192,138,114,.22)", color: priorityFocus === b.key ? C.copperLight : C.warm }}
                >
                  {priorityFocus === b.key ? "Filtre actif — retirer" : `Voir toutes (${b.items.length})`}
                </button>
              </div>
            ))}
          </div>
        </section>

        <section>
          <p className="mb-2 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            CHRONOLOGIE DES MISSIONS
          </p>
          <div className="flex flex-col gap-2 rounded-xl border p-3" style={{ borderColor: C.line, background: "rgba(19,22,27,.5)" }}>
            {activityFeed.length === 0 ? (
              <p className="py-4 text-center text-[10.5px]" style={{ color: C.faint }}>
                Aucune activité récente.
              </p>
            ) : (
              activityFeed.slice(0, 8).map((ev) => {
                const meta = KIND_META[ev.kind] ?? KIND_META.create;
                return (
                  <div key={ev.id} className="flex items-center gap-2.5 text-[10.5px]">
                    <span className="w-[34px] shrink-0" style={{ color: C.faint }}>
                      {ev.time}
                    </span>
                    <span style={{ color: meta.color }}>{meta.icon}</span>
                    <span style={{ color: C.ivory }}>{ev.agent}</span>
                    <span className="min-w-0 flex-1 truncate" style={{ color: C.muted }}>
                      {ev.action}
                    </span>
                    <span className="shrink-0 rounded-full border px-2 py-0.5 text-[8.5px]" style={{ borderColor: "rgba(192,138,114,.2)", color: C.faint }}>
                      {ev.dept}
                    </span>
                  </div>
                );
              })
            )}
          </div>
        </section>
      </div>

      <div className="hidden w-[clamp(240px,19vw,300px)] shrink-0 flex-col gap-3 min-[1200px]:flex">
        <div className="rounded-xl border p-3.5" style={{ borderColor: C.line, background: "rgba(19,22,27,.55)" }}>
          <div className="mb-2.5 flex items-center justify-between">
            <p className="text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
              FILTRES
            </p>
            <button
              type="button"
              onClick={() => {
                setSearch("");
                setProjectFilter("all");
                setStatusFilter("all");
                setPriorityFilter("all");
                setPriorityFocus(null);
              }}
              className="text-[9.5px]"
              style={{ color: C.copper }}
            >
              Réinitialiser
            </button>
          </div>
          <div className="flex flex-col gap-2.5">
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Rechercher une mission…"
              className="rounded-lg border bg-transparent px-2.5 py-1.5 text-[10.5px] outline-none"
              style={{ borderColor: C.line, color: C.ivory }}
            />
            <select value={projectFilter} onChange={(e) => setProjectFilter(e.target.value)} className="rounded-lg border bg-transparent px-2.5 py-1.5 text-[10.5px] outline-none" style={{ borderColor: C.line, color: C.warm }}>
              <option value="all">Tous les projets</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
            <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as "all" | TicketStatus)} className="rounded-lg border bg-transparent px-2.5 py-1.5 text-[10.5px] outline-none" style={{ borderColor: C.line, color: C.warm }}>
              <option value="all">Tous les statuts</option>
              {TICKET_STATUSES.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.label}
                </option>
              ))}
            </select>
            <select value={priorityFilter} onChange={(e) => setPriorityFilter(e.target.value as "all" | TicketPriority)} className="rounded-lg border bg-transparent px-2.5 py-1.5 text-[10.5px] outline-none" style={{ borderColor: C.line, color: C.warm }}>
              <option value="all">Toutes les priorités</option>
              {TICKET_PRIORITIES.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div className="rounded-xl border p-3.5" style={{ borderColor: C.line, background: "rgba(19,22,27,.55)" }}>
          <p className="mb-2.5 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            CHARGE DE TRAVAIL
          </p>
          <div className="flex flex-col gap-2">
            {agents.map((a) => {
              const load = STATUS_LOAD[statuses[a.id]?.status ?? "idle"];
              return (
                <div key={a.id} className="flex items-center gap-2">
                  <AgentAvatar agentId={a.id} name={a.name} size={20} />
                  <span className="min-w-0 flex-1 truncate text-[10px]" style={{ color: C.warm }}>
                    {a.name}
                  </span>
                  <span className="h-1 w-12 overflow-hidden rounded-full" style={{ background: "rgba(192,138,114,.15)" }}>
                    <span className="block h-full rounded-full" style={{ width: `${load}%`, background: C.copper }} />
                  </span>
                  <span className="w-8 shrink-0 text-right text-[9.5px]" style={{ color: C.ivory }}>
                    {load}%
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        <div className="rounded-xl border p-3.5" style={{ borderColor: C.line, background: "rgba(19,22,27,.55)" }}>
          <p className="mb-2.5 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            MISSIONS À RISQUE
          </p>
          {risks.length === 0 ? (
            <p className="text-[10px]" style={{ color: C.faint }}>
              Aucune mission à risque identifiée.
            </p>
          ) : (
            <div className="flex flex-col gap-2">
              {risks.map((r) => (
                <div key={r.id} className="rounded-lg border p-2" style={{ borderColor: "rgba(248,113,113,.2)" }}>
                  <div className="flex items-center justify-between gap-2">
                    <span className="min-w-0 flex-1 truncate text-[10.5px] font-medium" style={{ color: C.ivory }}>
                      {r.title}
                    </span>
                    <span
                      className="shrink-0 rounded-full px-1.5 py-px text-[8px]"
                      style={{ background: r.level === "Risque élevé" ? "rgba(248,113,113,.18)" : "rgba(192,138,114,.18)", color: r.level === "Risque élevé" ? "#f87171" : C.copperLight }}
                    >
                      {r.level}
                    </span>
                  </div>
                  <p className="text-[9px]" style={{ color: C.faint }}>
                    {r.detail}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="flex flex-col items-center gap-2 rounded-xl border p-3.5" style={{ borderColor: C.line, background: "rgba(19,22,27,.55)" }}>
          <p className="w-full text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            PERFORMANCE GLOBALE
          </p>
          <div className="relative h-[70px] w-[70px]">
            <svg width="70" height="70" viewBox="0 0 70 70">
              <circle cx="35" cy="35" r="29" fill="none" stroke="rgba(192,138,114,.15)" strokeWidth="5" />
              <circle
                cx="35"
                cy="35"
                r="29"
                fill="none"
                stroke={C.copper}
                strokeWidth="5"
                strokeLinecap="round"
                strokeDasharray={`${((efficiency / 100) * 2 * Math.PI * 29).toFixed(1)} ${(2 * Math.PI * 29).toFixed(1)}`}
                transform="rotate(-90 35 35)"
              />
            </svg>
            <span className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-[15px] font-semibold">{efficiency}%</span>
              <span className="text-[7px]" style={{ color: C.faint }}>
                Efficacité
              </span>
            </span>
          </div>
          <div className="flex w-full justify-between text-[9.5px]" style={{ color: C.faint }}>
            <span>
              Temps estimé <b style={{ color: C.ivory }}>{estimatedHours}h</b>
            </span>
            <span>
              Temps passé <b style={{ color: C.ivory }}>{spentHours}h</b>
            </span>
          </div>
        </div>
      </div>

      <CreateTicketModal open={createOpen} onOpenChange={setCreateOpen} projects={projects} defaultProjectId={createDefaultProject} onCreated={(t) => setTickets((prev) => [...prev, t])} agents={agents} />
    </div>
  );
}
