"use client";

import { useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { toast } from "sonner";
import {
  PRIORITY_STYLES,
  STATUS_STYLES,
  TICKET_STATUSES,
  TYPE_STYLES,
  type TicketPriority,
  type TicketStatus,
  type TicketType,
} from "@/components/tickets/tickets.constants";
import { updateTicket, type TicketWithProject } from "@/lib/tickets";
import { AgentAvatar } from "@/components/shared/agent-avatar";
import { getAgentsForBureau, type BureauKey } from "@/lib/agent-bureau";
import { cn } from "@/lib/utils";

interface MissionsKanbanProps {
  bureau: BureauKey;
  tickets: TicketWithProject[];
  loading: boolean;
  onTicketsChange: (tickets: TicketWithProject[]) => void;
}

/** Mockup's 4-column pipeline (Backlog/In Progress/In Review/Completed),
 * mapped to the real ticket statuses now that "in_review" exists
 * (TASTE DECISION #2, resolved by Emilie: real status, not a relabel).
 * `wont_fix` isn't a pipeline stage — it doesn't get a column here. */
const COLUMNS: { status: TicketStatus; label: string }[] = [
  { status: "open", label: "Backlog" },
  { status: "in_progress", label: "In Progress" },
  { status: "in_review", label: "In Review" },
  { status: "done", label: "Terminé" },
];

/** Pipeline-position progress — an honest proxy (where the card sits in the
 * board), not an invented per-task completion percentage. */
const COLUMN_PROGRESS: Record<TicketStatus, number> = {
  open: 10,
  in_progress: 45,
  in_review: 75,
  done: 100,
  wont_fix: 100,
};

export function MissionsKanban({ bureau, tickets, loading, onTicketsChange }: MissionsKanbanProps) {
  const teamMembers = getAgentsForBureau(bureau).slice(0, 3);
  const [pendingTicketId, setPendingTicketId] = useState<string | null>(null);

  async function advance(ticket: TicketWithProject, direction: 1 | -1) {
    if (pendingTicketId === ticket.id) return; // double-clic guard (CRITICAL GAP #3)
    const idx = COLUMNS.findIndex((c) => c.status === ticket.status);
    const nextIdx = idx + direction;
    if (nextIdx < 0 || nextIdx >= COLUMNS.length) return;
    const nextStatus = COLUMNS[nextIdx].status;

    const previousTickets = tickets;
    setPendingTicketId(ticket.id);
    // Optimistic update — le rollback générique (catch ci-dessous) couvre
    // aussi bien le 404 (ticket supprimé entre-temps, CRITICAL GAP #1) que
    // tout autre échec réseau (CRITICAL GAP #2) : le backend ne peut pas
    // structurellement émettre un 409 aujourd'hui (pas de champ version),
    // un seul mécanisme générique suffit pour les deux cas.
    onTicketsChange(
      tickets.map((t) => (t.id === ticket.id ? { ...t, status: nextStatus } : t))
    );
    try {
      await updateTicket(ticket.id, { status: nextStatus });
    } catch {
      onTicketsChange(previousTickets);
      toast.error(`Impossible de déplacer « ${ticket.title} »`);
    } finally {
      setPendingTicketId(null);
    }
  }

  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        {COLUMNS.map((c) => (
          <div key={c.status} className="h-64 animate-pulse rounded-xl border border-bronze-faint bg-obsidian/50" />
        ))}
      </div>
    );
  }

  return (
    <div className="flex snap-x snap-mandatory gap-3 overflow-x-auto pb-2 lg:grid lg:grid-cols-4 lg:overflow-visible">
      {COLUMNS.map((column, columnIdx) => {
        const columnTickets = tickets.filter((t) => t.status === column.status);
        return (
          <div
            key={column.status}
            role="group"
            aria-label={`${column.label}, ${columnTickets.length} ticket${columnTickets.length !== 1 ? "s" : ""}`}
            className="min-w-[80vw] shrink-0 snap-start rounded-xl border border-bronze-faint bg-obsidian-deep/40 sm:min-w-[280px] lg:min-w-0"
          >
            <div className="flex items-center justify-between border-b border-bronze-faint px-3 py-2.5">
              <span
                className={cn(
                  "rounded-full border px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide",
                  STATUS_STYLES[column.status]
                )}
              >
                {column.label}
              </span>
              <span className="text-[10px] text-titane/50">{columnTickets.length}</span>
            </div>

            <ul className="max-h-[28rem] space-y-2 overflow-y-auto p-2.5">
              {columnTickets.length === 0 ? (
                <li className="px-2 py-6 text-center text-xs text-titane/45">Aucun ticket</li>
              ) : (
                columnTickets.map((ticket) => {
                  const statusLabel =
                    TICKET_STATUSES.find((s) => s.id === ticket.status)?.label ?? ticket.status;
                  const typeStyle = TYPE_STYLES[ticket.type as TicketType];
                  const priorityStyle = PRIORITY_STYLES[ticket.priority as TicketPriority];
                  return (
                    <li
                      key={ticket.id}
                      className="rounded-lg border border-bronze-faint bg-obsidian/70 p-2.5"
                      aria-label={`Ticket : ${ticket.title}, statut ${statusLabel}, projet ${ticket.project_name ?? "?"}`}
                    >
                      <p className="text-sm leading-snug text-ivoire/90">{ticket.title}</p>
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {priorityStyle ? (
                          <span
                            className={cn(
                              "rounded-full border px-2 py-0.5 text-[9px] font-medium uppercase tracking-wide",
                              priorityStyle.badge
                            )}
                          >
                            {priorityStyle.label}
                          </span>
                        ) : null}
                        {typeStyle ? (
                          <span
                            className={cn(
                              "rounded-full border px-2 py-0.5 text-[9px] font-medium uppercase tracking-wide",
                              typeStyle.badge
                            )}
                          >
                            {typeStyle.label}
                          </span>
                        ) : null}
                        {ticket.project_name ? (
                          <span className="rounded-full border border-bronze-faint bg-obsidian-deep/60 px-2 py-0.5 text-[9px] text-titane/60">
                            {ticket.project_name}
                          </span>
                        ) : null}
                      </div>

                      <div className="mt-2.5 flex items-center justify-between">
                        <div className="flex -space-x-1.5">
                          {teamMembers.map((member) => (
                            <AgentAvatar
                              key={member.id}
                              agentId={member.id}
                              name={member.name}
                              size={20}
                              className="ring-1 ring-obsidian"
                            />
                          ))}
                        </div>
                        <span className="text-[9px] tabular-nums text-titane/50">
                          {COLUMN_PROGRESS[ticket.status as TicketStatus]}%
                        </span>
                      </div>
                      <div className="mt-1 h-1 overflow-hidden rounded-full bg-obsidian-deep">
                        <div
                          className="h-full rounded-full bg-bronze"
                          style={{ width: `${COLUMN_PROGRESS[ticket.status as TicketStatus]}%` }}
                        />
                      </div>

                      <div className="mt-2.5 flex items-center justify-between">
                        <button
                          type="button"
                          disabled={columnIdx === 0 || pendingTicketId === ticket.id}
                          onClick={() => void advance(ticket, -1)}
                          aria-label={`Reculer « ${ticket.title} » à l'étape précédente`}
                          className="flex h-11 w-11 items-center justify-center rounded-lg text-titane/60 transition-colors hover:bg-obsidian-deep hover:text-ivoire disabled:pointer-events-none disabled:opacity-0"
                        >
                          <ChevronLeft className="h-4 w-4" />
                        </button>
                        <button
                          type="button"
                          disabled={columnIdx === COLUMNS.length - 1 || pendingTicketId === ticket.id}
                          onClick={() => void advance(ticket, 1)}
                          aria-label={`Avancer « ${ticket.title} » à l'étape suivante`}
                          className="flex h-11 w-11 items-center justify-center rounded-lg text-bronze-bright transition-colors hover:bg-bronze/10 disabled:pointer-events-none disabled:opacity-0"
                        >
                          <ChevronRight className="h-4 w-4" />
                        </button>
                      </div>
                    </li>
                  );
                })
              )}
            </ul>
          </div>
        );
      })}
    </div>
  );
}
