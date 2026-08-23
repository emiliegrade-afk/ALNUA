"use client";

import { useEffect, useMemo, useState } from "react";
import { fetchTicketsList, type TicketWithProject } from "@/lib/tickets";
import { CreateTicketModal } from "@/components/tickets/create-ticket-modal";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { getAgentById, type BureauAgentDef } from "@/lib/agent-bureau";
import type { ConsoleActivityItem } from "@/lib/console/types";
import type { Project } from "@/lib/types";
import { C, KIND_META, formatDueDate } from "../app-v2/shared";

/* Idea Forge — tickets ouverts réels uniquement (type / priorité / échéance /
 * assignee). Plus de votes / catégories / ETA inventés. */

const TYPE_FILTERS = ["Toutes", "feature", "bug", "chore", "idea", "other"] as const;

export function BacklogTab({
  projects,
  agents,
  activityFeed,
}: {
  projects: Project[];
  agents: BureauAgentDef[];
  activityFeed: ConsoleActivityItem[];
}) {
  const [tickets, setTickets] = useState<TicketWithProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<(typeof TYPE_FILTERS)[number]>("Toutes");
  const [createOpen, setCreateOpen] = useState(false);

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
        if (!cancelled) {
          setTickets(all.filter((t) => ids.has(t.project_id) && t.status === "open"));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [projects]);

  const ideas = useMemo(() => {
    const list = tickets.filter(
      (t) => filter === "Toutes" || (t.type || "other").toLowerCase() === filter,
    );
    return [...list].sort((a, b) => {
      const pa = a.priority === "critical" ? 0 : a.priority === "high" ? 1 : 2;
      const pb = b.priority === "critical" ? 0 : b.priority === "high" ? 1 : 2;
      return pa - pb;
    });
  }, [tickets, filter]);

  if (loading) {
    return (
      <div
        className="flex min-h-[220px] flex-1 items-center justify-center rounded-xl text-[11px]"
        style={{ border: `1px solid ${C.line}`, color: C.faint }}
      >
        Chargement de l&apos;Idea Forge…
      </div>
    );
  }

  return (
    <div className="flex min-h-0 flex-1 gap-3 overflow-y-auto pb-2">
      <div className="flex min-w-0 flex-1 flex-col gap-3">
        <div className="flex items-center justify-between gap-3">
          <p className="text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            IDEA FORGE — ROBOTIQUE
          </p>
          <button
            type="button"
            onClick={() => setCreateOpen(true)}
            className="rounded-[18px] border px-3.5 py-1.5 text-[11px]"
            style={{
              borderColor: "rgba(224,155,106,.45)",
              background: "rgba(224,155,106,.12)",
              color: C.copperLight,
            }}
          >
            ＋ Nouvelle idée
          </button>
        </div>

        <div className="flex gap-2 overflow-x-auto">
          {TYPE_FILTERS.map((c) => (
            <button
              key={c}
              type="button"
              onClick={() => setFilter(c)}
              className="shrink-0 rounded-full border px-3 py-1 text-[10px]"
              style={{
                borderColor: filter === c ? C.copper : "rgba(224,155,106,.2)",
                background: filter === c ? "rgba(224,155,106,.15)" : "transparent",
                color: filter === c ? C.copperLight : C.warm,
              }}
            >
              {c}
            </button>
          ))}
        </div>

        {ideas.length === 0 ? (
          <div
            className="flex min-h-[180px] flex-1 items-center justify-center rounded-xl border text-[11px]"
            style={{ borderColor: C.line, color: C.faint }}
          >
            Aucun ticket ouvert.
          </div>
        ) : (
          <div className="grid grid-cols-[repeat(auto-fill,minmax(230px,1fr))] gap-2.5">
            {ideas.map((ticket) => {
              const due = ticket.due_date ? formatDueDate(ticket.due_date) : null;
              const assignee = ticket.assignee_agent_id
                ? getAgentById(ticket.assignee_agent_id)
                : undefined;
              return (
                <div key={ticket.id} className="flex flex-col gap-2 dept-instrument p-3">
                  <div className="flex items-center justify-between gap-2">
                    <span
                      className="rounded-full border px-1.5 py-px text-[8px]"
                      style={{ borderColor: "rgba(224,155,106,.22)", color: C.copperLight }}
                    >
                      {ticket.type || "ticket"}
                    </span>
                    <span className="text-[9.5px]" style={{ color: C.dim }}>
                      {ticket.priority || "—"}
                    </span>
                  </div>
                  <p className="text-[11.5px] font-medium" style={{ color: C.ivory }}>
                    {ticket.title}
                  </p>
                  <div className="grid grid-cols-2 gap-1 text-[9px]" style={{ color: C.faint }}>
                    <span>
                      Points{" "}
                      <b style={{ color: C.warm }}>
                        {ticket.story_points ?? "—"}
                      </b>
                    </span>
                    <span>
                      {due ? (
                        <>
                          Échéance{" "}
                          <b style={{ color: due.overdue ? "#f87171" : C.warm }}>
                            {due.label}
                          </b>
                        </>
                      ) : (
                        <>Échéance <b style={{ color: C.warm }}>—</b></>
                      )}
                    </span>
                  </div>
                  {assignee ? (
                    <div
                      className="flex items-center gap-1.5 border-t pt-1.5"
                      style={{ borderColor: C.lineSoft }}
                    >
                      <AgentAvatar agentId={assignee.id} name={assignee.name} size={16} />
                      <span className="truncate text-[9px]" style={{ color: C.faint }}>
                        Assigné : {assignee.name.split(" ")[0]}
                      </span>
                    </div>
                  ) : null}
                </div>
              );
            })}
          </div>
        )}
      </div>

      <div className="hidden w-[clamp(220px,17vw,270px)] shrink-0 flex-col gap-3 min-[1200px]:flex">
        <div className="dept-instrument p-3.5">
          <p className="mb-2.5 text-[9.5px] tracking-[1.5px]" style={{ color: C.faint }}>
            ACTIVITÉ RÉCENTE
          </p>
          {activityFeed.length === 0 ? (
            <p className="py-4 text-center text-[10px]" style={{ color: C.faint }}>
              Aucune activité récente.
            </p>
          ) : (
            <div className="flex flex-col gap-2.5">
              {activityFeed.slice(0, 8).map((ev) => {
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
              })}
            </div>
          )}
        </div>
      </div>

      <CreateTicketModal
        open={createOpen}
        onOpenChange={setCreateOpen}
        projects={projects}
        onCreated={(t) => setTickets((prev) => [...prev, t])}
        agents={agents}
      />
    </div>
  );
}
